import os
import glob
import urllib.request
import urllib.parse
import json

def main():
    token = os.environ.get('TG_TOKEN', '')
    chat_id = os.environ.get('TG_CHAT', '')
    tag = os.environ.get('RELEASE_TAG', 'v1.0.01')

    if not token or not chat_id:
        print("Telegram token or chat_id not provided. Skipping Telegram upload.")
        return

    caption = f"""<b>Mystic Kernel {tag} — Release</b>

• <b>Device</b>: OnePlus 9R (lemonades / SM8250)
• <b>ROM</b>: OxygenOS 14 (Android 14)
• <b>Kernel</b>: 4.19.157-perf-Mystic-9R-myzanori-{tag}
• <b>Status</b>: Boot Tested &amp; Verified (Working)
• <b>Root</b>: ReSukiSU v4.2.0-rc3
• <b>Hiding</b>: SUSFS v2.3.0
• <b>TCP Congestion</b>: BBR + FQ-CoDel
• <b>Camera</b>: 8/8 Sensors Operational
• <b>SELinux</b>: Enforcing
• <b>Developer</b>: @myzanori

<b>Changelog:</b>
<blockquote>
• Built for OxygenOS 14 (LE2101_14.0.0.2401 &amp; B100P01)
• ReSukiSU v4.2.0-rc3 with inline syscall hooks
• SUSFS v2.3.0 kernel-side path, mount, and kstat hiding
• BBR TCP Congestion Control &amp; FQ-CoDel queueing
• Full vendor module compatibility (35/35 modules loaded)
• Complete camera subsystem fix (8/8 sensors functional)
• Native F2FS compression and inlinecrypt support
</blockquote>"""

    zip_files = glob.glob('release_out/*.zip')
    if not zip_files:
        print("No release zip files found in release_out/")
        return

    for fpath in zip_files:
        filename = os.path.basename(fpath)
        print(f"Uploading {filename} to Telegram...")
        boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
        body = []
        body.append(f'--{boundary}\r\nContent-Disposition: form-data; name="chat_id"\r\n\r\n{chat_id}\r\n')
        body.append(f'--{boundary}\r\nContent-Disposition: form-data; name="parse_mode"\r\n\r\nHTML\r\n')
        body.append(f'--{boundary}\r\nContent-Disposition: form-data; name="caption"\r\n\r\n{caption}\r\n')
        body.append(f'--{boundary}\r\nContent-Disposition: form-data; name="document"; filename="{filename}"\r\nContent-Type: application/zip\r\n\r\n')
        
        with open(fpath, 'rb') as f:
            file_bytes = f.read()
            
        full_body = "".join(body).encode('utf-8') + file_bytes + f'\r\n--{boundary}--\r\n'.encode('utf-8')
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendDocument",
            data=full_body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
        )
        try:
            with urllib.request.urlopen(req) as resp:
                res_data = resp.read().decode('utf-8')
                print(f"Telegram upload success: {res_data}")
        except Exception as e:
            print(f"Telegram upload error: {e}")

if __name__ == '__main__':
    main()
