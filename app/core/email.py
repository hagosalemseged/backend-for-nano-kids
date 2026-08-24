import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.core.config import settings


def send_user_credentials(
    email: str,
    full_name: str | None,
    temporary_password: str,
):
    name = full_name or "User"

    subject = "Welcome to NanoKids"

    html_content = f"""
    <html>
        <body>
            <h2>Welcome to NanoKids</h2>

            <p>Hello {name},</p>

            <p>
                Your NanoKids account has been created.
            </p>

            <p>
                <strong>Login email:</strong><br>
                {email}
            </p>

            <p>
                <strong>Temporary password:</strong><br>
                {temporary_password}
            </p>

            <p>
                Please log in and change your password
                immediately.
            </p>

            <p>
                If you did not expect this account,
                please contact your administrator.
            </p>

            <br>

            <p>
                Regards,<br>
                NanoKids Team
            </p>
        </body>
    </html>
    """

    message = MIMEMultipart("alternative")

    message["Subject"] = subject

    message["From"] = (
        f"{settings.SMTP_FROM} "
        f"<{settings.SMTP_USERNAME}>"
    )

    message["To"] = email

    message.attach(
        MIMEText(
            html_content,
            "html",
        )
    )

    # -----------------------------------------------------
    # SMTP connection
    # -----------------------------------------------------

    with smtplib.SMTP(
        settings.SMTP_HOST,
        settings.SMTP_PORT,
    ) as server:

        server.starttls()

        server.login(
            settings.SMTP_USERNAME,
            settings.SMTP_PASSWORD,
        )

        server.sendmail(
            settings.SMTP_FROM,
            email,
            message.as_string(),
        )