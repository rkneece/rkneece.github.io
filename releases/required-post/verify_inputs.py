from pathlib import Path
import json,hashlib
root=Path(__file__).resolve().parent
for path,digest in json.loads((root/'REQUIRED_POST_RELEASE_ASSETS.json').read_text()).items():
 assert hashlib.sha256((root/path).read_bytes()).hexdigest()==digest,path
print('All reviewed input hashes match')
