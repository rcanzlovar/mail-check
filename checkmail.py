# checkmail-config.py 
# Bob Anzlovar 22-oct-2025 
# 
import imaplib
import email
import os
import re
import paramiko
import scp
import configparser
import smtplib
import sys
from datetime import datetime
from email.utils import parsedate_to_datetime, parseaddr
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# --- Read Configuration from config.ini ---
config = configparser.ConfigParser()
config_file = 'config.ini'

if not config.read(config_file):
    print(f"Error: Configuration file '{config_file}' not found.", file=sys.stderr)
    sys.exit(1) # Abort the script with an error code

# --- IMAP/SMTP Configuration ---
IMAP_SERVER = config['EMAIL']['IMAP_SERVER']
SMTP_SERVER = config['EMAIL']['SMTP_SERVER']
SMTP_PORT = config.getint('EMAIL', 'SMTP_PORT') # Use .getint() for numbers
SMTP_USERNAME = config['EMAIL']['SMTP_USERNAME']
SMTP_PASSWORD = config['EMAIL']['SMTP_PASSWORD']
FORWARDING_ADDRESS = config['EMAIL']['FORWARDING_ADDRESS']

# --- SCP Configuration ---
HOSTNAME = config['SCP']['HOSTNAME']
PORT = config.getint('SCP', 'PORT') # Use .getint() for numbers
USERNAME = config['SCP']['USERNAME']
PASSWORD = config['SCP']['PASSWORD']

# --- Directory Paths ---
LOCAL_DIRECTORY = config['PATHS']['LOCAL_DIRECTORY'] # This is './comments'
REMOTE_DIRECTORY = config['PATHS']['REMOTE_DIRECTORY']

# --- Utility Functions (unchanged) ---

def forward_uncategorized_email(raw_email_bytes, from_address, smtp_details):
    """Forwards an email that was deemed 'uncategorized'."""
    print(f"Forwarding uncategorized email to {smtp_details['forward_to']}...")
    try:
        original_msg = email.message_from_bytes(raw_email_bytes)
        original_subject = original_msg.get("Subject", "No Subject")
        new_msg = MIMEMultipart()
        new_msg['From'] = from_address
        new_msg['To'] = smtp_details['forward_to']
        new_msg['Subject'] = f"Fwd: Uncategorized Comment - {original_subject}"
        body = f"This email comment was processed but could not be categorized because the subject line did not contain a slug in parentheses.\n\nOriginal Subject: {original_subject}\n"
        new_msg.attach(MIMEText(body, 'plain'))
        attachment = MIMEApplication(raw_email_bytes, _subtype="message/rfc822")
        attachment.add_header('Content-Disposition', 'attachment', filename='original_email.eml')
        new_msg.attach(attachment)
        with smtplib.SMTP(smtp_details['server'], smtp_details['port']) as server:
            server.starttls()
            server.login(smtp_details['username'], smtp_details['password'])
            server.send_message(new_msg)
            print("Email forwarded successfully.")
    except Exception as e:
        print(f"❌ Error: Failed to forward email. Reason: {e}")

def sanitize_filename(name):
    s = re.sub(r'[^\w-]+', '_', name)
    return s.strip('_')

def get_email_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            cdispo = str(part.get('Content-Disposition'))
            if ctype == 'text/plain' and 'attachment' not in cdispo:
                body = part.get_payload(decode=True)
                return body.decode('utf-8', errors='replace')
    else:
        body = msg.get_payload(decode=True)
        return body.decode('utf-8', errors='replace')
    return ""

def parse_email_metadata(msg):
    """Parses headers from an email message and returns them in a dict."""
    metadata = {}
    try:
        dt_obj = parsedate_to_datetime(msg.get('Date'))
        metadata['dt_obj'] = dt_obj
        metadata['date_iso'] = dt_obj.strftime('%Y-%m-%d')
        metadata['date_comment'] = dt_obj.strftime('%e-%b-%Y %H:%M')
        metadata['timestamp'] = dt_obj.strftime("%Y%m%d%H%M%S")
    except (TypeError, ValueError):
        dt_obj = datetime.now()
        metadata['dt_obj'] = dt_obj
        metadata['date_iso'] = dt_obj.strftime('%Y-%m-%d')
        metadata['date_comment'] = dt_obj.strftime('%e-%b-%Y %H:%M')
        metadata['timestamp'] = dt_obj.strftime("%Y%m%d%H%M%S")
        print(f"Warning: Could not parse date header.")

    metadata['subject_full'] = msg.get("Subject", "No Subject")
    metadata['sender_full'] = msg.get('From', 'default@domain.com')
    
    sender_name, sender_email = parseaddr(metadata['sender_full'])
    metadata['sender_name'] = sender_name
    metadata['sender_email'] = sender_email
    metadata['sender_local'] = sender_email.split('@')[0] if '@' in sender_email else 'anonymous'
    
    return metadata

def save_comment_files(raw_email_data, metadata, lines, base_paths, slug):
    """Saves the .eml, .md, and .html files for a processed comment."""
    try:
        # --- 1. Save raw .eml file ---
        sanitized_email = sanitize_filename(metadata['sender_email'])
        eml_filename = f"{sanitized_email}-{metadata['timestamp']}-{slug}.eml"
        eml_filepath = os.path.join(base_paths['eml'], eml_filename)
        with open(eml_filepath, "wb") as f:
            f.write(raw_email_data)
        print(f"Successfully saved raw email: {eml_filepath}")

        # --- 2. Create MD file ---
        formatted_body_md = '\n\n'.join(line.strip() for line in lines if line.strip())
        title_md = metadata['subject_full']
        subject_match = re.match(r'\((.*?)\)(.*)', metadata['subject_full'])
        if subject_match:
            title_md = subject_match.group(2).strip()
        
        md_content = f"---\ntitle: {title_md}\ndate: {metadata['date_iso']}\npublished: true\nslug: {slug}\n---\n\n{formatted_body_md}"
        md_filename = f"{metadata['date_iso']}_{slug}.md"
        
        # Create the specific slug directory for markdown
        slug_dir_md = os.path.join(base_paths['md'], slug)
        os.makedirs(slug_dir_md, exist_ok=True)
        md_filepath = os.path.join(slug_dir_md, md_filename)
        
        with open(md_filepath, "w", encoding='utf-8') as f:
            f.write(md_content)
        print(f"Successfully saved markdown file: {md_filepath}")

        # --- 3. Create/Append HTML comment file ---
        file_path = os.path.join(base_paths['base'], f"{slug}.html") # This uses LOCAL_DIRECTORY
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                f.write(f"\n<h3>Comments</h3>\n")
            print(f"File '{file_path}' created.")
        
        formatted_body_html = '\n'.join(f"<p>{line.strip()}</p>" for line in lines if line.strip())
        with open(file_path, 'a') as f:
            f.write(f"<h4>{title_md}</h4>\n")
            f.write(f"{metadata['date_comment']} <i>{metadata['sender_local']}</i>\n")
            f.write(formatted_body_html + '\n')
            f.write("\n")
        print(f"New HTML comment appended to {file_path}.")

    except Exception as e:
        print(f"Error saving files for slug '{slug}': {e}")


def process_email(mail, num, base_paths, smtp_details):
    """Fetches, parses, and processes a single email."""
    try:
        print(f"\n--- Processing email ID {num.decode()} ---")
        status, data = mail.fetch(num, "(RFC822)")
        if status != 'OK':
            print(f"ERROR fetching email {num.decode()}")
            return # Skip this email

        raw_email_data = data[0][1]
        msg = email.message_from_bytes(raw_email_data)
        
        # Parse all metadata
        metadata = parse_email_metadata(msg)

        # --- Slug Parsing and Forwarding Logic ---
        slug_match = re.search(r'\((.*?)\)', metadata['subject_full'])
        if slug_match:
            slug = sanitize_filename(slug_match.group(1))
        else:
            slug = "uncategorized"
        print(f"Subject: '{metadata['subject_full']}' -> slug: '{slug}'")

        if slug == "uncategorized":
            forward_uncategorized_email(raw_email_data, smtp_details['username'], smtp_details)
        
        # --- Body Parsing and File Saving ---
        body_raw = get_email_body(msg)
        if not body_raw:
            print("Warning: Could not find text body. Skipping file creation.")
        else:
            body_match = re.search(r'------(.*?)------', body_raw, re.DOTALL)
            if body_match:
                content_between_dashes = body_match.group(1)
                lines = content_between_dashes.splitlines()
                
                # Call the new function to save all files
                save_comment_files(raw_email_data, metadata, lines, base_paths, slug)
            else:
                print("Warning: Dashed line separators '------' not found in email body. Skipping file creation.")

        # --- Mark Email for Deletion ---
        print(f"Marking email ID {num.decode()} for deletion.")
        mail.store(num, '+FLAGS', r'(\Deleted)')

    except Exception as e:
        print(f"❌ CRITICAL ERROR processing email ID {num.decode()}: {e}")
        print("This email will be skipped.")


def fetch_emails(email_address, password, imap_server='mail.rcanzlovar.com'):
    """Connects to IMAP, loops through emails, and calls process_email."""
    print("Connecting to mail server...")
    try:
        mail = imaplib.IMAP4_SSL(imap_server, port=993)
        mail.login(email_address, password)
        mail.select("inbox")
        print("Connection successful.")

        status, messages = mail.search(None, "ALL")
        if status != "OK":
            print("No messages found!")
            return False

        email_ids = messages[0].split()
        print(f"Found {len(email_ids)} emails to process.")
        if not email_ids:
            return False # No emails to process

        # --- *** PATHS MODIFIED AS REQUESTED *** ---
        # LOCAL_DIRECTORY (from config) is the base for HTML comments and SCP upload.
        # md and eml paths are at the same level, but not uploaded.
        base_paths = {
            'base': LOCAL_DIRECTORY,  # e.g., './comments'
            'md': 'mdcomments',       # e.g., './mdcomments'
            'eml': 'emails'           # e.g., './emails'
        }
        
        # Create all needed directories
        os.makedirs(base_paths['base'], exist_ok=True)
        os.makedirs(base_paths['md'], exist_ok=True)
        os.makedirs(base_paths['eml'], exist_ok=True)
        # --- *** END OF MODIFICATION *** ---

        # --- Setup SMTP details for forwarding ---
        smtp_details = {
            "server": SMTP_SERVER,
            "port": SMTP_PORT,
            "username": SMTP_USERNAME,
            "password": SMTP_PASSWORD,
            "forward_to": FORWARDING_ADDRESS
        }

        # --- Process each email ---
        for num in email_ids:
            process_email(mail, num, base_paths, smtp_details)

        # --- Expunge and Logout ---
        print("\n--- Expunging all marked emails from server ---")
        mail.expunge()
        print("Emails deleted.")
        mail.logout()
        print("Logout successful.")
        return True

    except Exception as e:
        print(f"An error occurred: {e}")
        # Ensure logout on failure
        try:
            mail.logout()
        except:
            pass
        return False

# --- SCP Upload Function (unchanged) ---
def upload_directory_with_password():
    """Uploads ONLY the LOCAL_DIRECTORY (e.g., 'comments')."""
    ssh_client = None
    try:
        print(f"Connecting to {HOSTNAME}...")
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(hostname=HOSTNAME, port=PORT, username=USERNAME, password=PASSWORD)
        print("✅ Connection successful.")
        with scp.SCPClient(ssh_client.get_transport()) as scp_client:
            print(f"Uploading files from '{LOCAL_DIRECTORY}' to '{REMOTE_DIRECTORY}'...")
            scp_client.put(LOCAL_DIRECTORY, remote_path=REMOTE_DIRECTORY, recursive=True)
        print("🚀 Upload complete!")
    except Exception as e:
        print(f"❌ An error occurred: {e}")
    finally:
        if ssh_client:
            ssh_client.close()
            print("Connection closed.")

# --- Main execution block (unchanged) ---
if __name__ == "__main__":
    if not os.path.isdir(LOCAL_DIRECTORY):
        print(f"Warning: Local directory '{LOCAL_DIRECTORY}' not found. It will be created.")

    # Hardcoded credentials are still here!
    if fetch_emails("comments@rcanzlovar.com", "$Comments4Blogsites!"):
        upload_directory_with_password()
