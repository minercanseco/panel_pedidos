import datetime
import uuid
from decimal import Decimal, ROUND_HALF_UP
import base64
from io import BytesIO
from PIL import Image
import qrcode
import barcode
from barcode.writer import ImageWriter
from capturar_documento.herramientas.enviar_correos.cfdi_ticket import CFDITicket
import os
import re
import sys
from pathlib import Path

class GenerarPDFFactura:
    def __init__(self, parametros, base_de_datos, utilerias):
        self._parametros = parametros
        self._base_de_datos = base_de_datos
        self._utilerias = utilerias
        self._ticket = CFDITicket()

        self._nombre_archivo = None
        self._document_id = 0
        self._marca_de_agua_id = 4

        self._user_id = self._parametros.id_usuario
        self._user_name = self._base_de_datos.buscar_nombre_de_usuario(self._user_id)

    @property
    def nombre_archivo(self) -> str:
        return self._nombre_archivo

    @nombre_archivo.setter
    def nombre_archivo(self, value: str):
        if not value or not str(value).strip():
            raise ValueError("nombre_archivo no puede ser vacío.")
        self._nombre_archivo = str(value).strip()

    @property
    def marca_de_agua_id(self):
        return self._marca_de_agua_id

    @marca_de_agua_id.setter
    def marca_de_agua_id(self, value):
        self._marca_de_agua_id = value

    @property
    def document_id(self):
        return self._document_id

    @document_id.setter
    def document_id(self, value):
        self._document_id = int(value or 0)

    def _sanitizar_nombre_archivo(self, nombre: str) -> str:
        # evita caracteres raros en Windows/Unix
        nombre = re.sub(r'[^A-Za-z0-9_.()\-\ ]', '_', (nombre or '').strip())
        nombre = nombre.strip().strip('.')
        return nombre or "cfdi"

    def _asegurar_ext_html(self, nombre: str) -> str:
        root, ext = os.path.splitext(nombre)
        return nombre if ext else (nombre + ".html")

    def _resolver_plantilla_cfdi(self):
        nombre = 'cfdi_ticket.html'
        modulo = Path(__file__).resolve().parent
        ejecutable = Path(sys.executable).resolve().parent
        meipass = getattr(sys, '_MEIPASS', None)

        candidatos = []
        plantilla_configurada = getattr(self, 'cfdi_ticket', None)
        if plantilla_configurada:
            candidatos.append(Path(plantilla_configurada))

        candidatos.extend((
            modulo / nombre,
            ejecutable / nombre,
            ejecutable / '_internal' / nombre,
            ejecutable / '_internal' / 'capturar_documento'
            / 'herramientas' / 'enviar_correos' / nombre,
            Path.cwd() / nombre,
            Path.cwd() / 'capturar_documento' / 'herramientas'
            / 'enviar_correos' / nombre,
        ))

        if meipass:
            raiz_bundle = Path(meipass)
            candidatos.extend((
                raiz_bundle / nombre,
                raiz_bundle / 'capturar_documento' / 'herramientas'
                / 'enviar_correos' / nombre,
                raiz_bundle / 'capturar_documento' / 'plantillas' / nombre,
            ))

        revisados = []
        for candidato in candidatos:
            candidato = candidato.resolve()
            texto = str(candidato)
            if texto in revisados:
                continue
            revisados.append(texto)
            if candidato.is_file():
                return texto

        raise FileNotFoundError(
            'No se encontró {}. Rutas revisadas:\n{}'.format(
                nombre,
                '\n'.join(revisados),
            )
        )

    def generar_archivo_cfdi(self, motivo_id=7):
        # Validaciones mínimas
        if not self.document_id:
            raise ValueError("document_id no está seteado (es 0).")
        if not self.nombre_archivo:
            raise ValueError("nombre_archivo no está seteado.")

        # Funciona desde código fuente, One Directory y One File.
        plantilla_path = self._resolver_plantilla_cfdi()
        self._ticket.set_plantilla(plantilla_path)

        # Datos CFDI
        info = self._buscar_info_factura(self.document_id) or {}
        placeholders = info.get("placeholders", {}) or {}
        partidas = info.get("detalle", []) or []
        mostrar_pagado = bool(info.get("mostrar_pagado", False))

        # Remisión / Factura
        es_remision_doc = 0 if placeholders.get("TipoCFD", 'FACTURA') == 'FACTURA' else 1

        # Descuento (nota: ojo si placeholders['DescuentoCayal'] ya viene formateado como string "0.00")
        hay_descuento = self._utilerias.redondear_valor_cantidad_a_decimal(
            placeholders.get("DescuentoCayal", 0)
        )

        self._ticket.set_marca_agua(motivo_id=self._marca_de_agua_id)
        uuid_archivo  = str(uuid.uuid4())
        placeholders_extra = {
            'uuid': uuid_archivo,
            'ES_REMISION': es_remision_doc,
            'TextoRemision': 'REMISIÓN',
            'MOSTRAR_PAGADO': mostrar_pagado,
            'MOSTRAR_DESCUENTO': hay_descuento
        }

        # Render
        self._ticket.set_datos(**placeholders, **placeholders_extra)
        self._ticket.set_partidas(partidas)
        html = self._ticket.generar_html()

        # Condicionales
        if not mostrar_pagado:
            html = re.sub(r"<!--IF_PAGADO-->.*?<!--END_IF-->\s*", "", html, flags=re.DOTALL)

        if hay_descuento == 0:
            html = re.sub(r"<!--IF_DESCUENTO-->.*?<!--END_IF-->\s*", "", html, flags=re.DOTALL)

        if es_remision_doc == 0:
            html = re.sub(r"<!--IF_NO_REMISION-->.*?<!--END_IF_NO_REMISION-->\s*", "", html, flags=re.DOTALL)
        else:
            html = re.sub(r"<!--IF_REMISION-->.*?<!--END_IF-->\s*", "", html, flags=re.DOTALL)

        # Guardado (usa el método correcto del ticket; ajusta el nombre según tu CFDITicket real)
        # Si tu CFDITicket tiene _obtener_directorio_salida, usa ese.
        if hasattr(self._ticket, "obtener_directorio_salida"):
            base = self._ticket.obtener_directorio_salida(temporal=True)
        else:
            base = self._ticket.obtener_directorio_salida(temporal=True)

        nombre = self._sanitizar_nombre_archivo(self.nombre_archivo)
        nombre = self._asegurar_ext_html(nombre)
        ruta = os.path.join(base, nombre)

        with open(ruta, "w", encoding="utf-8") as f:
            f.write(html or "")

        return ruta

    def _definir_marca_agua_id(self, place_holders):
        pass


    def _buscar_info_factura(self, document_id):
        # ---------- Consulta de generales ----------
        generales_documento = self._base_de_datos.fetchall("""
            SELECT
                -- Identificación y fechas
                CONCAT(ISNULL(D.FolioPrefix, ''), ISNULL(D.Folio, ''))                   AS folio,
                CAST(D.CreatedOn AS date)                                                AS FechaExpedicion,
                CONVERT(char(5), D.CreatedOn, 108)                                       AS HoraExpedicion, -- HH:mm
                D.FolioPrefix                                                            AS Serie,
                D.Folio,

                -- Totales y leyenda
                CAST(ISNULL(D.CambioCayal,    0) AS DECIMAL(18,2))                       AS CambioCayal,
                CAST(ISNULL(D.SubTotal,       0) AS DECIMAL(18,2))                       AS SubTotal,
                CAST(ISNULL(Tax.IVA_T,        0) AS DECIMAL(18,2))                       AS IVA,
                CAST(ISNULL(Tax.IEPS_T,       0) AS DECIMAL(18,2))                       AS IEPS,
                CAST(ISNULL(D.Total,          0) AS DECIMAL(18,2))                       AS Total,
                CAST(ISNULL(D.DescuentoCayal, 0) AS DECIMAL(18,2))                       AS DescuentoCayal,
                CAST(ISNULL(D.Balance,        0) AS DECIMAL(18,2))                       AS Saldo,
                CASE WHEN ISNULL(D.DescuentoCayal, 0) <> 0 THEN 'Descuento:' ELSE '' END AS DescuentoCayalTitulo,
                ISNULL(D.TotalLetter, '')                                                AS CantidadConLetra,
                ISNULL(D.Comments, '')                                                   AS Comments,

                -- Datos CFDI
                CASE WHEN D.chkCustom1 = 1 THEN 'REMISION' ELSE 'FACTURA' END AS TipoCFD,
                CFD.CFDITimbreImage,
                CFD.MetodoPago,
                CFD.FormaPago,
                CFD.ReceptorUsoCFDI,

                CASE WHEN D.chkCustom1 = 0 THEN E.CompanyTypeName ELSE '616 - Sin obligaciones fiscales' END AS RegimenReceptor,
                CASE WHEN D.chkCustom1 = 0 THEN CFD.CFDISelloDigitalSAT ELSE '' END                           AS SelloDigitalSATCayal,
                CASE WHEN D.chkCustom1 = 0 THEN CFD.CFDSello           ELSE '' END                           AS SelloDigitalCayal,
                CASE WHEN D.chkCustom1 = 0 THEN CFD.CFDCadenaOriginal  ELSE '' END                           AS CadenaOriginalCayal,
                CASE WHEN CFD.CFDTipoRelacion        IS NULL THEN '' ELSE CFD.CFDTipoRelacion       END      AS TipoRelacion,
                CASE WHEN CFD.CFDUUIDRelacionados    IS NULL THEN '' ELSE CFD.CFDUUIDRelacionados   END      AS CFDIRelacionados,
                CASE WHEN CFD.CFDTipoRelacion        IS NULL THEN '' ELSE 'TIPO RELACIÓN:'           END      AS TipoRelacionTitulo,
                CASE WHEN CFD.CFDUUIDRelacionados    IS NULL THEN '' ELSE 'CFDI RELACIONADOS:'   END      AS CFDIRelacionadosTitulo,
                CFD.CFDIFolioFiscal                                                                 AS Uuid,
                CFD.CFDINumSerieCertificadoSAT                                                      AS NoCertificadoSAT,
                CFD.CFDIFechaCertificacion                                                          AS FechaTimbrado,
                OCFD.CSDnoCertificado                                                               AS NoCertificado,

                -- Receptor (nombre/RFC)
                CASE WHEN D.BusinessEntityID = 8179 THEN E2.OfficialName ELSE E.OfficialName END     AS ReceptorCayal,
                CASE 
                    WHEN D.BusinessEntityID = 8179 
                         THEN CASE WHEN ISNULL(E2.Custom2, 0) = 1 THEN 1 ELSE 0 END
                    ELSE CASE WHEN ISNULL(E.Custom2, 0) = 1 THEN 1 ELSE 0 END
                END AS PapelID,
                CASE 
                    WHEN D.BusinessEntityID = 8179 
                         THEN CASE WHEN ISNULL(E2.Impresiones, 1) = 1 THEN 1 ELSE 2 END
                    ELSE CASE WHEN ISNULL(E.Impresiones, 1) = 1 THEN 1 ELSE 2 END
                END AS Impresiones,
                CASE WHEN D.chkCustom1 = 1 THEN 'XAXX010101000' ELSE EM.OfficialNumber END           AS RFCReceptorCayal,

                -- Receptor (domicilio fiscal mostrado)
                CASE
                    WHEN X.AddressDetailID = 0 AND D.BusinessEntityID = 8179 THEN EM2.AddressFiscalStreet
                    WHEN X.AddressDetailID = 0 AND D.BusinessEntityID <> 8179 THEN EM.AddressFiscalStreet
                    ELSE ADT.Street
                END AS ReceptorCalleCayal,

                CASE
                    WHEN X.AddressDetailID = 0 AND D.BusinessEntityID = 8179 THEN EM2.AddressFiscalExtNumber
                    WHEN X.AddressDetailID = 0 AND D.BusinessEntityID <> 8179 THEN EM.AddressFiscalExtNumber
                    ELSE ADT.ExtNumber
                END AS ReceptorDomicilioNoExteriorCayal,

                CASE
                    WHEN X.AddressDetailID = 0 AND D.BusinessEntityID = 8179 THEN EM2.AddressFiscalIntNumber
                    WHEN X.AddressDetailID = 0 AND D.BusinessEntityID <> 8179 THEN EM.AddressFiscalIntNumber
                    ELSE ADT.IntNumber
                END AS ReceptorDomicilioNoInteriorCayal,

                CASE
                    WHEN X.AddressDetailID = 0 AND D.BusinessEntityID = 8179 THEN EM2.AddressFiscalCity
                    WHEN X.AddressDetailID = 0 AND D.BusinessEntityID <> 8179 THEN EM.AddressFiscalCity
                    ELSE ADT.City
                END AS ReceptorDomicilioColoniaCayal,

                CASE
                    WHEN X.AddressDetailID = 0 AND D.BusinessEntityID = 8179 THEN EM2.AddressFiscalZipCode
                    WHEN X.AddressDetailID = 0 AND D.BusinessEntityID <> 8179 THEN EM.AddressFiscalZipCode
                    ELSE ADT.ZipCode
                END AS ReceptorDomicilioCodigoPostalCayal,

                -- Comentarios fiscales (bloque mostrado)
                CASE
                    WHEN X.AddressDetailID = 0 AND D.BusinessEntityID = 8179 THEN EM2.AddressFiscalComments
                    WHEN X.AddressDetailID = 0 AND D.BusinessEntityID <> 8179 THEN EM.AddressFiscalComments
                    ELSE ADT.Comments
                END AS FiscalAddresMainInfoCommentsCayal,

                -- Teléfonos
                CASE
                    WHEN X.AddressDetailID = 0 AND D.BusinessEntityID = 8179 THEN EM2.BusinessEntityPhone
                    WHEN X.AddressDetailID = 0 AND D.BusinessEntityID <> 8179 THEN EM.BusinessEntityPhone
                    ELSE ADT.Telefono
                END AS ReceptorTelefonoEmpresa,

                CASE
                    WHEN X.AddressDetailID <> 0 AND ISNULL(ADT.Telefono, '') <> '' THEN ADT.Telefono
                    ELSE OCC.ChannelValue
                END AS CelularCliente,

                -- Usuarios
                U.UserName  AS Capturista,
                UT.UserName AS TimbradoPor,
                dbo.fn_GenerarCodigoEAN13DesdeDocumento(D.DocumentID) AS CodigoEAN13,
                OCE.OfficialName AS EmisorNombre,
                OCE.CompanyTypeName AS RegimenEmisor,
                OCEM.OfficialNumber RFCEmisor,
                ISNULL(D.Custom3,0) ZoneID
            FROM docDocument AS D
            LEFT JOIN docDocumentTax               AS Tax  ON Tax.DocumentID        = D.DocumentID
            LEFT JOIN docDocumentCFD               AS CFD  ON CFD.DocumentID        = D.DocumentID
            LEFT JOIN orgBusinessEntity            AS E    ON E.BusinessEntityID    = D.BusinessEntityID
            LEFT JOIN orgBusinessEntityMainInfo    AS EM   ON EM.BusinessEntityID   = E.BusinessEntityID

            LEFT JOIN docDocumentExtra             AS X    ON X.DocumentID          = D.DocumentID
            LEFT JOIN orgAddressDetail             AS ADT  ON ADT.AddressDetailID   = X.AddressDetailID
            LEFT JOIN docDocumentExt               AS EX   ON EX.IDExtra            = D.DocumentID
            LEFT JOIN orgBusinessEntityMainInfo    AS EM2  ON EM2.BusinessEntityID  = EX.CustomerID
            LEFT JOIN orgBusinessEntity            AS E2   ON E2.BusinessEntityID   = EX.CustomerID

            LEFT JOIN engUser                      AS U    ON U.UserID              = D.CreatedBy
            LEFT JOIN engUser                      AS UT   ON UT.UserID             = CFD.UserID

            LEFT JOIN orgBusinessEntityCFD         AS OCFD ON OCFD.BusinessEntityID = D.OwnedBusinessEntityID
            LEFT JOIN orgBusinessEntity            AS OCE ON OCFD.BusinessEntityID = OCE.BusinessEntityID
            LEFT JOIN orgBusinessEntityMainInfo    AS OCEM ON OCE.BusinessEntityID = OCEM.BusinessEntityID

            OUTER APPLY (
                SELECT TOP (1) oc.ChannelValue
                FROM orgCommunicationChannel AS oc
                WHERE oc.BusinessEntityID = D.BusinessEntityID
                  AND oc.ChannelTypeID    = 3
                ORDER BY oc.ChannelTypeID DESC
            ) AS OCC
            WHERE D.DocumentID = ?;
        """, (document_id,))

        # ---------- Partidas ----------
        partidas_documento = self._base_de_datos.fetchall(
            'SELECT * FROM [dbo].[zvwBuscarPartidasDocumentoCayal-DocumentID](?) ORDER BY DocumentItemID',
            (document_id,)
        )
        partidas_documento_impuestos = self._utilerias.agregar_impuestos_productos(partidas_documento)

        # ---------- Normalización de generales ----------
        g = (generales_documento[0] if generales_documento else {})

        emisor = self._safe_str(g.get('EmisorNombre', ''))
        regimen_emisor = self._safe_str(g.get('RegimenEmisor', ''))
        rfc_emisor = self._safe_str(g.get('RFCEmisor', ''))
        folio = self._safe_str(g.get('folio'))
        fecha_expedicion = g.get('FechaExpedicion')
        hora_expedicion = self._safe_str(g.get('HoraExpedicion'))
        serie = self._safe_str(g.get('Serie'))
        folio_num = self._safe_str(g.get('Folio'))
        zone_id = g.get('ZoneID', 0)
        papel_id = g.get('PapelID', 0)
        impresiones = g.get('Impresiones', 1)

        pagado_cayal = g.get('CambioCayal', Decimal('0'))
        subtotal = g.get('SubTotal', Decimal('0'))
        iva_total = g.get('IVA', Decimal('0'))
        ieps_total = g.get('IEPS', Decimal('0'))
        total = g.get('Total', Decimal('0'))
        descuento = g.get('DescuentoCayal', Decimal('0'))
        saldo = g.get('Saldo', Decimal('0'))
        descuento_titulo = self._safe_str(g.get('DescuentoCayalTitulo'))
        cantidad_con_letra = self._safe_str(g.get('CantidadConLetra'))
        comentarios = self._safe_str(g.get('Comments'))

        # CFDI extras (opcionales en placeholders por si tu plantilla los usa)
        metodo_pago = self._safe_str(g.get('MetodoPago'))
        forma_pago = self._safe_str(g.get('FormaPago'))
        uso_cfdi = self._safe_str(g.get('ReceptorUsoCFDI'))
        regimen_receptor = self._safe_str(g.get('RegimenReceptor'))

        sello_sat = self._safe_str(g.get('SelloDigitalSATCayal'))
        sello_cfd = self._safe_str(g.get('SelloDigitalCayal'))
        cadena_original = self._safe_str(g.get('CadenaOriginalCayal'))
        tipo_relacion = self._safe_str(g.get('TipoRelacion'))
        uuids_relacionados = self._safe_str(g.get('CFDIRelacionados'))
        uuid = self._safe_str(g.get('Uuid'))
        no_cert_sat = self._safe_str(g.get('NoCertificadoSAT'))
        fecha_timbrado = self._safe_str(g.get('FechaTimbrado'))
        no_cert_emisor = self._safe_str(g.get('NoCertificado'))
        tipo_cfd = g.get('TipoCFD', 'FACTURA')
        qr_base_64 = self._safe_str(g.get('CFDITimbreImage', ''))
        codigo_ean_13 = self._safe_str(g.get('CodigoEAN13', ''))

        qr_data_uri = (f"data:image/png;base64,{qr_base_64.replace('\n', '').replace('\r', '')}"
                       if qr_base_64 and not qr_base_64.startswith('data:') else qr_base_64)

        # Asegurar 13 dígitos exactos para EAN-13
        codigo_ean_13_clean = ''.join(ch for ch in codigo_ean_13 if ch.isdigit())[:13]
        # Receptor
        receptor_nombre = self._safe_str(g.get('ReceptorCayal'))
        rfc_receptor = self._safe_str(g.get('RFCReceptorCayal'))

        rec_calle = self._safe_str(g.get('ReceptorCalleCayal'))
        rec_no_ext = self._safe_str(g.get('ReceptorDomicilioNoExteriorCayal'))
        rec_no_int = self._safe_str(g.get('ReceptorDomicilioNoInteriorCayal'))
        rec_colonia = self._safe_str(g.get('ReceptorDomicilioColoniaCayal'))
        rec_cp = self._safe_str(g.get('ReceptorDomicilioCodigoPostalCayal'))

        fiscal_comments = self._safe_str(g.get('FiscalAddresMainInfoCommentsCayal'))
        tel_empresa = self._safe_str(g.get('ReceptorTelefonoEmpresa'))
        tel_celular = self._safe_str(g.get('CelularCliente'))

        capturista = self._safe_str(g.get('Capturista'))
        timbrado_por = self._safe_str(g.get('TimbradoPor'))

        # Fecha string para placeholder
        fecha_str = '' if not fecha_expedicion else str(fecha_expedicion)

        # ---------- Detalle reutilizable ----------
        detalle = self._crear_detalle_partidas(partidas_documento_impuestos)
        total_pzas = sum([reg['Quantity'] for reg in partidas_documento])

        # ---------- Bloque de pago condicional (igual que ticket) ----------
        pagado = Decimal(str(pagado_cayal or 0))
        cambio_cayal = (Decimal(str(pagado_cayal or 0)) - Decimal(str(total)))

        hay_pago = (pagado > 0 or Decimal(str(cambio_cayal or 0)) > 0)

        # ---------- Placeholders (alineados a ticket) ----------
        placeholders = {
            # Generales
            'EmisorNombre': emisor,
            'EmisorRFC': rfc_emisor,
            'EmisorRegimen': regimen_emisor,
            'EmisorDomicilio': 'Av. Gustavo Diaz Ordaz N 207 Col. La Ermita, C.P. 24020',
            'folio': folio,
            'Serie': serie,
            'Folio': folio_num,
            'FechaExpedicion': fecha_str,
            'HoraExpedicion': hora_expedicion,
            'FechaImpresion': datetime.datetime.now().strftime('%Y-%m-%d'),
            'HoraImpresion': datetime.datetime.now().strftime('%H:%M'),
            'LugarExpedicion': 'San Francisco de Campeche, Campeche',

            # Totales / Impuestos
            'SubTotal': self._fmt_money(subtotal),
            'IEPS': self._fmt_money(ieps_total),
            'IVA': self._fmt_money(iva_total),
            'Total': self._fmt_money(total),
            'DescuentoCayalTitulo': descuento_titulo,
            'DescuentoCayal': self._fmt_money(descuento),
            'TotalPzas': str(total_pzas),
            'CantidadConLetra': cantidad_con_letra,
            'Comentarios': comentarios,
            'ZoneID': zone_id,
            'PapelID': papel_id,
            'Impresiones': impresiones,
            'Saldo': saldo,

            # Pago (condicional como en ticket)
            'cliente_pago_ticket': 'Pagado' if hay_pago else '',
            'pagado_ticket': self._fmt_money(pagado) if hay_pago else '',
            'cliente_cambio_ticket': 'Cambio' if hay_pago else '',
            'cambio_venta': self._fmt_money(cambio_cayal) if hay_pago else '',

            # CFDI opcionales
            'MetodoPago': metodo_pago,
            'FormaPago': forma_pago,
            'ReceptorUsoCFDI': uso_cfdi,
            'ReceptorRegimen': regimen_receptor,
            'SelloDigitalSATCayal': sello_sat,
            'SelloDigitalCayal': sello_cfd,
            'CadenaOriginalCayal': cadena_original,
            'TipoRelacion': tipo_relacion,
            'CFDIRelacionados': uuids_relacionados,
            'Uuid': uuid,
            'NoCertificadoSAT': no_cert_sat,
            'FechaTimbrado': fecha_timbrado,
            'NoCertificado': no_cert_emisor,
            'TipoCFD': tipo_cfd,

            'QrBase64': qr_data_uri,
            'CodigoEAN13': self._make_ean13_data_url(codigo_ean_13_clean),

            # Receptor
            'ReceptorCayal': receptor_nombre,
            'RFCReceptorCayal': rfc_receptor,
            'ReceptorCalleCayal': rec_calle,
            'ReceptorDomicilioNoExteriorCayal': rec_no_ext,
            'ReceptorDomicilioNoInteriorCayal': rec_no_int,
            'ReceptorDomicilioColoniaCayal': rec_colonia,
            'ReceptorDomicilioCodigoPostalCayal': rec_cp,

            'FiscalAddresMainInfoCommentsCayal': fiscal_comments,
            'ReceptorTelefonoEmpresa': tel_empresa,
            'CelularCliente': tel_celular,

            # Usuarios
            'Capturista': capturista,
            'TimbradoPor': timbrado_por,
            'ImpresoPor': self._user_name
        }

        return {
            'placeholders': placeholders,
            'detalle': detalle,  # lista para el bloque <DETAIL>
            'mostrar_pagado': hay_pago
        }

    def _fmt_money(self, v):
        """Devuelve string con 2 decimales, nulos como '0.00'."""
        if v is None:
            v = Decimal('0')
        if not isinstance(v, Decimal):
            v = Decimal(str(v))
        return str(v.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

    def _fmt_qty(self, v):
        """Cantidad compacta: quita ceros a la derecha (1.0000 -> '1'; 0.2500 -> '0.25')."""
        if v is None:
            return '0'
        d = Decimal(str(v))
        d = d.normalize()  # elimina ceros innecesarios
        s = format(d, 'f')  # evita notación científica
        if '.' in s:
            s = s.rstrip('0').rstrip('.')
        return s if s else '0'

    def _safe_str(self, s):
        return '' if s is None else str(s)

    def _img_pil_to_data_url_png(self, img: Image.Image) -> str:
        buf = BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        return f"data:image/png;base64,{b64}"

    def _make_qr_data_url(self, texto: str) -> str:
        qr = qrcode.QRCode(
            version=None, box_size=3, border=2,
            error_correction=qrcode.constants.ERROR_CORRECT_M
        )
        qr.add_data(texto or "")
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        return self._img_pil_to_data_url_png(img)

    def _make_ean13_data_url(self, ean13_digits: str) -> str:
        digits = ''.join(ch for ch in str(ean13_digits or '') if ch.isdigit())[:13]
        if len(digits) != 13:
            raise ValueError("EAN-13 debe contener exactamente 13 dígitos.")
        ean = barcode.get('ean13', digits, writer=ImageWriter())
        buf = BytesIO()
        # Desactiva el texto para evitar cargar fuente TTF
        ean.write(buf, options={
            "write_text": False,  # <--- CLAVE
            "module_height": 12.0,
            "font_size": 8,  # inofensivo si write_text=False
            "text_distance": 1  # "
        })
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        return f"data:image/png;base64,{b64}"

    def _crear_detalle_partidas(self, partidas):
        """
        Construye la lista de partidas para el bloque <DETAIL>.
        Cada item incluye: Cantidad, Descripcion, PrecioUnCIVA, ImporteCIVA.
        """
        detalle = []
        for it in (partidas or []):
            qty = it.get('cantidad') if it.get('cantidad') is not None else it.get('Quantity', 0)
            qty_dec = Decimal(str(qty or 0))
            total_renglon = Decimal(str(it.get('total', 0) or 0))
            clave = it.get('ProductKey')

            if qty_dec == 0:
                precio_c_iva = total_renglon
            else:
                precio_c_iva = (total_renglon / qty_dec).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)

            detalle.append({
                'Cantidad': self._fmt_qty(qty_dec),
                'ClaveUnidad': it.get('ClaveUnidad', 'H87'),
                'Clave': clave,
                'Descripcion': self._safe_str(it.get('Description') or it.get('ProductName') or ''),
                'PrecioUnCIVA': self._fmt_money(precio_c_iva),
                'ImporteCIVA': self._fmt_money(total_renglon),
                'PrecioUnSIVA': self._fmt_money(it.get('UnitPrice'))
            })
        return detalle

    def html_a_pdf(self, ruta_html: str, ruta_pdf: str):
        import os
        import winreg
        from playwright.sync_api import sync_playwright

        def _buscar_browser_exe():
            # 1) Rutas típicas
            candidatos = [
                # Edge
                r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"),

                # Chrome
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
            ]
            for p in candidatos:
                if p and os.path.exists(p):
                    return p

            # 2) Registro de Windows (App Paths)
            reg_keys = [
                # Edge
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe"),
                (winreg.HKEY_LOCAL_MACHINE,
                 r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe"),

                # Chrome
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"),
                (winreg.HKEY_LOCAL_MACHINE,
                 r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"),
            ]

            for root, subkey in reg_keys:
                try:
                    with winreg.OpenKey(root, subkey) as k:
                        val, _ = winreg.QueryValueEx(k, "")
                        if val and os.path.exists(val):
                            return val
                except OSError:
                    pass

            return None

        # --- Normalización de rutas ---
        ruta_html = os.path.abspath(ruta_html)
        ruta_pdf = os.path.abspath(ruta_pdf)
        os.makedirs(os.path.dirname(ruta_pdf), exist_ok=True)

        browser_exe = _buscar_browser_exe()
        if not browser_exe:
            raise FileNotFoundError(
                "No se encontró Edge ni Chrome instalados en el sistema."
            )

        with sync_playwright() as p:
            browser = p.chromium.launch(
                executable_path=browser_exe,
                headless=True
            )
            page = browser.new_page()
            page.goto(
                "file:///" + ruta_html.replace("\\", "/"),
                wait_until="load"
            )
            page.pdf(
                path=ruta_pdf,
                format="A4",
                print_background=True
            )
            browser.close()

        return ruta_pdf
