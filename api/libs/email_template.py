from setting import settings


def render_branded_email(
    subject: str,
    body_html: str,
    recipient_email: str = "",
    recipient_name: str = "",
    action_text: str = "",
    action_url: str = ""
) -> str:
    domain = getattr(settings, "DOMAIN_NAME", "kluda.app")
    app_url = f"https://app.{domain}" if "localhost" not in domain else "http://localhost:3000"
    support_url = f"https://support.{domain}" if "localhost" not in domain else "http://localhost:3000/support"

    button_markup = ""
    if action_text and action_url:
        button_markup = f"""
        <table border="0" cellpadding="0" cellspacing="0" style="margin: 24px 0;">
            <tr>
                <td align="center" style="border-radius: 8px; background-color: #059669;">
                    <a href="{action_url}" target="_blank" style="font-size: 14px; font-weight: 700; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #ffffff; text-decoration: none; padding: 12px 26px; border-radius: 8px; display: inline-block;">
                        {action_text} &rarr;
                    </a>
                </td>
            </tr>
        </table>
        """

    return f"""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{subject}</title>
    <style type="text/css">
        body {{ margin: 0; padding: 0; background-color: #f4f4f5; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; -webkit-font-smoothing: antialiased; }}
        table {{ border-collapse: collapse; }}
        img {{ border: 0; outline: none; text-decoration: none; }}
        a {{ color: #059669; text-decoration: underline; }}
        p {{ margin: 0 0 16px 0; line-height: 1.6; color: #334155; font-size: 15px; }}
        h1, h2, h3 {{ color: #0f172a; margin: 0 0 16px 0; font-weight: 700; line-height: 1.3; }}
        h1 {{ font-size: 22px; }}
        h2 {{ font-size: 18px; }}
        h3 {{ font-size: 16px; }}
        ul, ol {{ margin: 0 0 16px 0; padding-left: 22px; color: #334155; font-size: 15px; line-height: 1.6; }}
        li {{ margin-bottom: 6px; }}
        blockquote {{ margin: 16px 0; padding: 14px 18px; border-left: 4px solid #059669; background-color: #f8fafc; color: #1e293b; border-radius: 0 8px 8px 0; }}
        table.data-table {{ width: 100% !important; border-collapse: collapse; margin: 16px 0; }}
        table.data-table th, table.data-table td {{ border: 1px solid #e2e8f0; padding: 10px 14px; font-size: 14px; color: #334155; text-align: left; }}
        table.data-table th {{ background-color: #f8fafc; font-weight: 600; color: #0f172a; }}
    </style>
</head>
<body style="margin: 0; padding: 0; background-color: #f4f4f5;">
    <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f4f4f5; padding: 32px 12px;">
        <tr>
            <td align="center">
                <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; background-color: #ffffff; margin: 0 auto; border-radius: 12px; overflow: hidden; border: 1px solid #e4e4e7; box-shadow: 0 4px 16px rgba(0,0,0,0.06);">
                    <tr>
                        <td style="background-color: #0f172a; padding: 28px 32px; text-align: left;">
                            <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
                                <tr>
                                    <td>
                                        <table role="presentation" border="0" cellpadding="0" cellspacing="0">
                                            <tr>
                                                <td style="width: 36px; height: 36px; border-radius: 8px; background-color: #10b981; text-align: center; vertical-align: middle; font-size: 18px; font-weight: 900; color: #09090b; font-family: monospace;">K</td>
                                                <td style="padding-left: 12px;">
                                                    <span style="font-size: 20px; font-weight: 800; color: #ffffff; letter-spacing: -0.5px;">Kluda</span>
                                                    <span style="font-size: 10px; font-weight: 700; color: #10b981; background-color: rgba(16,185,129,0.15); border: 1px solid rgba(16,185,129,0.3); padding: 2px 6px; border-radius: 4px; margin-left: 8px; vertical-align: middle;">RETAIL POS</span>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                    <td align="right" style="font-size: 12px; color: #94a3b8; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
                                        Merchant Update
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <tr>
                        <td style="padding: 36px 32px; background-color: #ffffff; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
                            {body_html}
                            {button_markup}
                        </td>
                    </tr>

                    <tr>
                        <td style="padding: 24px 32px; background-color: #f8fafc; border-top: 1px solid #e2e8f0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
                            <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
                                <tr>
                                    <td style="font-size: 12px; color: #64748b; line-height: 1.5;">
                                        You are receiving this official communication as a registered store owner or administrator on the <strong>Kluda POS Platform</strong>.
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding-top: 16px; font-size: 11px; color: #94a3b8; border-top: 1px solid #e2e8f0; margin-top: 16px;">
                                        <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
                                            <tr>
                                                <td>
                                                    &copy; Kluda Retail Inc. All rights reserved.
                                                </td>
                                                <td align="right">
                                                    <a href="{app_url}" style="color: #64748b; margin-right: 12px; text-decoration: none;">Merchant Portal</a>
                                                    <a href="{support_url}" style="color: #64748b; text-decoration: none;">Help & Support</a>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
