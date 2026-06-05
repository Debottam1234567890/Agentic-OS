import sys
sys.path.insert(0, '/Users/sandeep/Agentic_OS')
from kernel import client
from vision.analyzer import analyze_image
print('Calling analyze_image...')
try:
    res = analyze_image('/Users/sandeep/Agentic_OS/sandbox/vision_scratch.png', client, 'What do you see?')
    print('Success:', res)
except Exception as e:
    print('Error:', e)
