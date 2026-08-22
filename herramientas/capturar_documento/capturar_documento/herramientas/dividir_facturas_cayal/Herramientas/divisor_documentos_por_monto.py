class DivisorDocumentosPorMonto:
    """
    Lógica pura: no toca UI, no toca self._modelo, no lee inputs.
    Todo lo que necesita se lo pasas por argumentos/callbacks.

    Comportamiento clave:
    - al_centavo=True:
        * Ignora reglas de producto (equivalencias/caja/huevo y no-divisible por ClaveUnidad).
        * Permite partir cualquier partida para clavar el monto del plan en centavos (2 decimales),
          sin usar redondear_qty_fn.
        * NO restringe la cantidad (qty) a 3 decimales: usa un step fino para poder clavar centavos.
    - al_centavo=False:
        * Respeta reglas originales (equivalencias/caja/huevo, no-divisible != KGM) y redondeos opcionales.
        * Mantiene step de qty a 0.001 como antes.
    """

    def __init__(
        self,
        convertir_decimal,
        crear_partida_con_impuestos,
        equivalencia_especial_fn=None,
        redondear_qty_fn=None,
    ):
        self.to_dec = convertir_decimal
        self.crear_partida = crear_partida_con_impuestos
        self.equiv_fn = equivalencia_especial_fn
        self.redondear_qty_fn = redondear_qty_fn

    def dividir(self, partidas, plan_montos, al_centavo=True):
        to_dec = self.to_dec
        plan = self._normalizar_plan(plan_montos)

        CENT = to_dec("0.01")

        # ===================== CAMBIO CLAVE =====================
        # - Antes: STEP_QTY fijo a 0.001 => limita a 3 decimales.
        # - Ahora:
        #   * al_centavo=True  -> step fino (sin restricción práctica a 3 decimales)
        #   * al_centavo=False -> step original 0.001
        STEP_QTY = to_dec("0.0000001") if al_centavo else to_dec("0.001")

        # ===================== helper para consistencia en centavos =====================
        def _dec_capacidad(x):
            x = to_dec(x)
            return x.quantize(CENT) if al_centavo else x

        # ---------------- Helpers mínimos ----------------
        def _get_qty_key(p):
            return "Quantity" if "Quantity" in p else ("cantidad" if "cantidad" in p else None)

        def _get_qty(p):
            k = _get_qty_key(p)
            return to_dec(p.get(k, 0)) if k else to_dec(0)

        def _set_qty(p, qty):
            k = _get_qty_key(p)
            if not k:
                p["Quantity"] = qty
            else:
                p[k] = qty

        def _clave_unidad(p):
            return (p.get("ClaveUnidad") or p.get("clave_unidad") or "").strip()

        def _es_no_divisible(p):
            return _clave_unidad(p) != "KGM"

        def _nombre_producto(p):
            return (p.get("ProductName") or p.get("Producto") or "").strip()

        def _product_id(p):
            try:
                return int(p.get("ProductID", 0) or 0)
            except Exception:
                return 0

        def _normalizar_para_calculo(p):
            base = dict(p)

            if "UnitPrice" not in base and "Precio" in base:
                base["UnitPrice"] = base["Precio"]

            qty = _get_qty(base)
            base["Quantity"] = qty
            if "cantidad" in base:
                del base["cantidad"]

            for k in (
                "precio",
                "subtotal",
                "iva",
                "ieps",
                "impuestos",
                "total",
                "retenciones",
                "cantidad_piezas",
                "clave_unidad",
                "clave_sat",
                "Subtotal",
                "Total",
            ):
                if k in base:
                    del base[k]

            return base

        def _total_con_impuestos_raw(p):
            p_calc = _normalizar_para_calculo(p)
            p_imp = self.crear_partida(p_calc)
            return to_dec(p_imp.get("total", 0))

        def _total_con_impuestos(p):
            # En modo al_centavo, siempre cuantizamos total a centavos
            return _dec_capacidad(_total_con_impuestos_raw(p))

        # --------- equivalencias especiales ----------
        def _equiv_especial(p):
            if not self.equiv_fn:
                return None
            pid = _product_id(p)
            if pid <= 0:
                return None
            try:
                eq = self.equiv_fn(pid)
            except Exception:
                eq = None
            return eq if eq else None

        def _tiene_caja(p):
            return "caja" in _nombre_producto(p).lower()

        def _es_huevo(p):
            return "huevo" in _nombre_producto(p).lower()

        def _chunk_qty_especial(p, eq):
            """
            Regla de 'caja': aplica a:
              - huevo
              - productos cuyo nombre incluya "caja"
            El tamaño del chunk lo toma de eq[1].
            """
            if not eq:
                return None
            if _es_huevo(p) or _tiene_caja(p):
                try:
                    q = to_dec(eq[1])
                    return q if q > 0 else None
                except Exception:
                    return None
            return None

        # --------- Split helper: binaria + preferencia a centavos exactos ----------
        def _buscar_qty_para_limite(partida_base, qty_max, limite_total):
            """
            Retorna best_qty (<= qty_max) tal que:
              - total(best_qty) <= limite_total
              - si al_centavo: minimiza gap en centavos (lim2 - t2), prefiriendo gap==0
              - si no al_centavo: maximiza qty sin pasarse
            """
            qty_max = to_dec(qty_max)
            if qty_max <= 0:
                return to_dec(0)

            lo = to_dec(0)
            hi = qty_max
            best = to_dec(0)

            best_gap_cent = None
            lim2 = _dec_capacidad(limite_total).quantize(CENT)

            def _q_step(x):
                # cuantiza hacia abajo a múltiplos de STEP_QTY (sin float)
                return (x / STEP_QTY).to_integral_value(rounding="ROUND_FLOOR") * STEP_QTY

            # Iteraciones suficientes incluso con step fino
            for _ in range(80):
                mid = _q_step((lo + hi) / to_dec(2))

                if mid <= 0:
                    hi = mid
                    continue

                tentativa = dict(partida_base)
                _set_qty(tentativa, mid)
                t = _total_con_impuestos(tentativa)  # ya viene cuantizado a centavos si al_centavo

                if t <= _dec_capacidad(limite_total):
                    if al_centavo:
                        t2 = t.quantize(CENT)
                        gap = lim2 - t2  # >= 0
                        if (best_gap_cent is None) or (gap < best_gap_cent) or (gap == best_gap_cent and mid > best):
                            best_gap_cent = gap
                            best = mid
                        lo = mid + STEP_QTY
                    else:
                        best = mid
                        lo = mid + STEP_QTY
                else:
                    hi = mid - STEP_QTY

            # Microajuste final cuando al_centavo:
            # probar un vecindario (en STEP_QTY) alrededor de best para encontrar gap==0 si existe
            if al_centavo and best > 0:
                objetivo = _dec_capacidad(limite_total).quantize(CENT)

                # probamos +-N steps alrededor del mejor
                N = 20  # 20 micro-steps hacia arriba/abajo (ajusta si quieres)
                mejor = best
                mejor_gap = None

                for i in range(-N, N + 1):
                    q = best + (to_dec(i) * STEP_QTY)
                    if q <= 0 or q > qty_max:
                        continue

                    tentativa = dict(partida_base)
                    _set_qty(tentativa, q)
                    t = _total_con_impuestos(tentativa)
                    if t > _dec_capacidad(limite_total):
                        continue

                    gap = objetivo - t.quantize(CENT)
                    if (mejor_gap is None) or (gap < mejor_gap) or (gap == mejor_gap and q > mejor):
                        mejor_gap = gap
                        mejor = q
                        if mejor_gap == 0:
                            break

                best = mejor

            return best

        # ---------------- Armado de documentos ----------------
        documento = 1
        documentos = {documento: []}

        monto_doc = _dec_capacidad(plan(1))
        total_en_proceso = _dec_capacidad(monto_doc)

        def _abrir_nuevo_doc():
            nonlocal documento, documentos, total_en_proceso, monto_doc

            documento += 1
            documentos[documento] = []

            try:
                nuevo_monto = plan(documento)
            except Exception:
                nuevo_monto = monto_doc  # fallback seguro

            monto_doc = _dec_capacidad(nuevo_monto if nuevo_monto is not None else 0)
            total_en_proceso = _dec_capacidad(monto_doc)

        for partida in (partidas or []):
            partida_restante = dict(partida)

            while True:
                qty_rest = _get_qty(partida_restante)
                if qty_rest <= 0:
                    break

                total_partida = _total_con_impuestos(partida_restante)
                if total_partida <= 0:
                    break

                eq = _equiv_especial(partida_restante)
                no_divisible = _es_no_divisible(partida_restante)

                # ===================== MODO AL CENTAVO =====================
                if al_centavo:
                    eq = None
                    no_divisible = False
                else:
                    if (
                        eq
                        and (not _es_huevo(partida_restante))
                        and (not _tiene_caja(partida_restante))
                        and (_clave_unidad(partida_restante) == "KGM")
                        and (total_partida > _dec_capacidad(plan(documento)))
                    ):
                        eq = None

                # ===================== REGLA CAJA (HUEVO o nombre contiene "caja") =====================
                if eq and (_es_huevo(partida_restante) or _tiene_caja(partida_restante)):
                    chunk_qty = _chunk_qty_especial(partida_restante, eq)
                    if chunk_qty:
                        while qty_rest > 0:
                            if qty_rest < chunk_qty:
                                tail = dict(partida_restante)
                                _set_qty(tail, qty_rest)
                                tail_total = _total_con_impuestos(tail)

                                if tail_total <= total_en_proceso:
                                    documentos[documento].append(tail)
                                    total_en_proceso = _dec_capacidad(total_en_proceso - tail_total)
                                    qty_rest = to_dec(0)
                                    break

                                _abrir_nuevo_doc()
                                documentos[documento].append(tail)
                                total_en_proceso = _dec_capacidad(total_en_proceso - tail_total)
                                qty_rest = to_dec(0)
                                break

                            this_qty = chunk_qty
                            chunk = dict(partida_restante)
                            _set_qty(chunk, this_qty)
                            chunk_total = _total_con_impuestos(chunk)

                            if chunk_total > total_en_proceso:
                                _abrir_nuevo_doc()

                            documentos[documento].append(chunk)
                            total_en_proceso = _dec_capacidad(total_en_proceso - chunk_total)
                            qty_rest = qty_rest - this_qty

                        break  # consumida por chunks/cola

                # ===================== NO DIVISIBLE o ESPECIAL NO HUEVO/CAJA (pieza completa) =====================
                if no_divisible or (eq and not _es_huevo(partida_restante) and not _tiene_caja(partida_restante)):
                    if total_partida > total_en_proceso:
                        _abrir_nuevo_doc()
                    documentos[documento].append(partida_restante)
                    total_en_proceso = _dec_capacidad(total_en_proceso - total_partida)
                    break

                # ===================== DIVISIBLE (KGM o forzado por al_centavo) =====================
                if total_partida <= total_en_proceso:
                    documentos[documento].append(partida_restante)
                    total_en_proceso = _dec_capacidad(total_en_proceso - total_partida)
                    break

                # Split (doc con contenido)
                if documentos[documento]:
                    qty = _get_qty(partida_restante)
                    if qty <= 0:
                        break

                    limite_total = total_en_proceso
                    total_full_raw = _total_con_impuestos_raw(partida_restante)
                    if total_full_raw <= 0 or limite_total <= 0:
                        _abrir_nuevo_doc()
                        continue

                    ratio = (limite_total / total_full_raw) if total_full_raw > 0 else to_dec(0)
                    qty_guess = qty * ratio
                    if qty_guess <= 0:
                        _abrir_nuevo_doc()
                        continue

                    if (not al_centavo) and self.redondear_qty_fn:
                        try:
                            qty_guess = self.redondear_qty_fn(qty_guess)
                        except Exception:
                            pass

                    # En al_centavo, NO limitar por qty_guess
                    qty_max = qty if al_centavo else qty_guess
                    best = _buscar_qty_para_limite(partida_restante, qty_max, limite_total)

                    if best > 0:
                        parcial = dict(partida_restante)
                        _set_qty(parcial, best)
                        tpar = _total_con_impuestos(parcial)
                        documentos[documento].append(parcial)
                        total_en_proceso = _dec_capacidad(total_en_proceso - tpar)

                        restante = dict(partida_restante)
                        _set_qty(restante, qty - best)

                        _abrir_nuevo_doc()
                        partida_restante = restante
                        continue

                    _abrir_nuevo_doc()
                    documentos[documento].append(partida_restante)
                    total_en_proceso = _dec_capacidad(total_en_proceso - _total_con_impuestos(partida_restante))
                    break

                # Doc vacío y excede: partir contra el monto del doc (plan(doc))
                qty = _get_qty(partida_restante)
                if qty <= 0:
                    break

                limite_total = _dec_capacidad(plan(documento))
                total_full_raw = _total_con_impuestos_raw(partida_restante)
                ratio = (limite_total / total_full_raw) if total_full_raw > 0 else to_dec(0)
                qty_guess = qty * ratio

                if qty_guess <= 0:
                    documentos[documento].append(partida_restante)
                    total_en_proceso = _dec_capacidad(total_en_proceso - total_partida)
                    break

                if (not al_centavo) and self.redondear_qty_fn:
                    try:
                        qty_guess = self.redondear_qty_fn(qty_guess)
                    except Exception:
                        pass

                # En al_centavo, NO limitar por qty_guess
                qty_max = qty if al_centavo else qty_guess
                best = _buscar_qty_para_limite(partida_restante, qty_max, limite_total)

                if best > 0:
                    parcial = dict(partida_restante)
                    _set_qty(parcial, best)
                    tpar = _total_con_impuestos(parcial)
                    documentos[documento].append(parcial)
                    total_en_proceso = _dec_capacidad(total_en_proceso - tpar)

                    restante = dict(partida_restante)
                    _set_qty(restante, qty - best)

                    _abrir_nuevo_doc()
                    partida_restante = restante
                    continue

                documentos[documento].append(partida_restante)
                total_en_proceso = _dec_capacidad(total_en_proceso - total_partida)
                break

        if documentos.get(documento) == []:
            documentos.pop(documento, None)

        return documentos

    def _normalizar_plan(self, plan_montos):
        to_dec = self.to_dec

        if callable(plan_montos):
            return plan_montos

        if isinstance(plan_montos, (list, tuple)):
            montos = [to_dec(x) for x in plan_montos if x is not None]
            if not montos:
                raise ValueError("plan_montos vacío")

            def _plan(doc_index):
                i = doc_index - 1
                return montos[i] if i < len(montos) else montos[-1]

            return _plan

        monto_unico = to_dec(plan_montos)

        def _plan(_doc_index):
            return monto_unico

        return _plan