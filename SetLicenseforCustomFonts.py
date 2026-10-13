# MenuTitle: Set License for Custom Fonts
# -*- coding: utf-8 -*-
__doc__="""
Sets License and Trademark property with dynamic placeholders for Custom Fonts
"""

from vanilla import Window, EditText, TextBox, Button
from GlyphsApp import Glyphs, Message
import re


def buildLicenseTexts(family_name, client_name):
    return {
        "English": f"""When using the {family_name} fonts, you agree to use them exclusively in branding and communication materials related to {client_name} and are not authorised to use them for any other purpose.

Modifying, adapting, altering, converting, translating, or otherwise changing the {family_name} font software is not permitted without written authorisation from Naipe Foundry.

Sending or sharing the {family_name} fonts with anyone or any organisation, or any third party that has not been directly contracted by {client_name} as a supplier, partner, franchisee, contractor, or otherwise associated, is not allowed.""",

        "Portuguese": f"""Ao utilizar as fontes digitais {family_name}, você aceita usá-las exclusivamente em materiais de marca e comunicação relacionados a {client_name} e reconhece que não está autorizado a usá-las para nenhum outro propósito.

Não é permitido modificar, adaptar, alterar, converter, traduzir ou de qualquer outra forma modificar o software da fonte digital {family_name} sem autorização por escrito da Naipe Foundry.

Não é permitido enviar ou compartilhar as fontes {family_name} com qualquer pessoa ou organização, ou com qualquer terceiro que não tenha sido contratado diretamente por {client_name} como fornecedor, parceiro, franqueado, contratado ou de qualquer outra forma associado.""",

        "Spanish": f"""Al utilizar las tipografías digitales {family_name}, aceptas utilizarlas exclusivamente en materiales de marca y comunicación relacionados con {client_name} y reconoces que no estás autorizado a utilizarlas para ningún otro propósito.

No se permite modificar, adaptar, alterar, convertir, traducir o de cualquier otra manera modificar el software de tipografía digital {family_name} sin la autorización por escrito de Naipe Foundry.

No está permitido enviar o compartir las tipografías {family_name} con ninguna persona u organización, o cualquier tercero que no haya sido contratado directamente por {client_name} como proveedor, socio, franquiciado, contratista o de cualquier otra manera asociado."""
    }


def cleanFamilyName(name):
    # Strip a trailing " Beta", " Beta 2", " Alpha", " Alpha 3" (needs a space before it,
    # so names like "Alphabeta" are left alone).
    return re.sub(
        r'\s+(beta|alpha)(\s*\d+)?$',
        '',
        name or "",
        flags=re.IGNORECASE
    ).strip()


def okCallback(sender):
    client_name = w.client_name_input.get().strip()

    if not client_name:
        Message("Please enter the client's full legal name.", "❌ Missing Client Name")
        return

    # Font may have been closed while the window was open
    font = Glyphs.font
    if not font:
        Message("Please open a font before running this script.", "❌ No Font Open")
        return

    # Save the client name for next run
    Glyphs.defaults["com.naipe.SetLicenseLastClientName"] = client_name

    family_name = cleanFamilyName(font.familyName)
    license_texts = buildLicenseTexts(family_name, client_name)

    # --- Set License (localized) ---
    # Clear existing "licenses" entries, then write dflt (English), PTG-BR (Brazilian Portuguese), ESP.
    # font.properties is a read-only Python proxy (no .remove), so go through
    # the underlying Cocoa array via key-value coding instead.
    properties_array = font.mutableArrayValueForKey_("properties")
    for prop in list(properties_array):
        if prop.key == "licenses":
            properties_array.removeObject_(prop)

    font.setProperty_value_languageTag_("licenses", license_texts["English"], "dflt")
    font.setProperty_value_languageTag_("licenses", license_texts["Portuguese"], "PTG-BR")
    font.setProperty_value_languageTag_("licenses", license_texts["Spanish"], "ESP")

    # --- Set Trademark ---
    font.trademark = f"{family_name} is a trademark of Naipe Foundry. All rights reserved."

    Glyphs.showNotification(
        "✅ Font Info Updated",
        "Licenses overwritten and Trademark set successfully."
    )

    w.close()


# --- Check for an open font before showing the window ---
if not Glyphs.font:
    Message("Please open a font before running this script.", "❌ No Font Open")
else:
    last_client_name = Glyphs.defaults["com.naipe.SetLicenseLastClientName"] or ""

    w = Window((380, 170), "📝 Set License for Custom Fonts")

    w.instruction = TextBox(
        (10, 10, -10, 40),
        "⚠️ Make sure to input the client's full legal name."
    )

    w.client_name_input = EditText((10, 60, -10, 22), last_client_name)

    w.okButton = Button(
        (125, 100, 140, 30),
        "✅ Apply License",
        callback=okCallback
    )

    w.disclaimer = TextBox(
        (10, 135, -10, 20),
        "ℹ️ Existing licenses will be overwritten.",
        sizeStyle="small"
    )

    w.open()
