import errno
import argparse
import os
import sys
from urllib.parse import urlparse

from jinja2 import Environment, PackageLoader

from req import HTTPRequest

LANGS = {
    'py': {
        'description': 'Python requests template',
        'template_file':'py.j2'
    },
    'js': {
        'description': 'Node script using requests (gonna use fetch soon)',
        'template_file': 'node.j2'
    }
}

def gen(request, template):
    env = Environment(
        loader=PackageLoader('templates')
    )
    template = env.get_template(template)

    if request.path.index('/')== 0:
        print('[+] Relative URI, enter scheme, hostname and port to generate url')
        host = None
        port = None
        host_header_value = request.headers.get('host', None)
        if host_header_value:
            if ':' not in host_header_value:
                host = host_header_value
            else:
                host = host_header_value.split(':')[0]
                port = int(host_header_value.split(':')[1])

            scheme = input('[+] Scheme (http/https): ')
            if host:
                hostname_input = input(
                    f'[+] Hostname \'{host}\' detected in Host header, Use it? [Y/N] ')
                if hostname_input == 'n' or hostname_input == 'N':
                    host = None
            if not host:
                host = input('[+] Enter hostname: ')
            if port:
                port_input = input(
                    f'[+] Port {port} found in Host header, Use this? [Y/N] ')
                if port_input == 'n' or port_input == 'N':
                    port = None
            if not port:
                port = int(input('[+] Enter port: '))
        else:
            parsed = urlparse(request.path)
            scheme = parsed.scheme
            host = parsed.hostname
            port = parsed.port
            if not port:
                if scheme == 'http':
                    port = 80
                elif scheme == 'https':
                    port = 443
            request.path = parsed.path
            if parsed.query:
                request.path += '?{}'.format(parsed.query)
        
        return template.render(
            headers=request.headers,
            data=request.data,
            cookies=request.cookies,
            method=request.command,
            uri=request.path,
            scheme=scheme,
            host=host,
            port=port,
        )
def main():
    parser = argparse.ArgumentParser('Usage: %prog -i [file]')
    parser.add_argument('-i', '--input', dest='input_file', type='string',
                        help='Input file containing the request')
    parser.add_argument('-o', '--output', dest='output_file', type='string', help='Output file to contain outputted code')
    parser.add_argument('-l', '--language', dest='lang', type='string', help='Language of template (default: py)', default='py')
    parsed = parser.parse_args()

    if not parsed.input_file:
        print(parser.usage)
        exit(0)
    
    output_file = None
    if parsed.output_file is not None:
        if os.path.dirname(parsed.output_file):
            if not os.path.exists(os.path.dirname(parsed.output_file)):
                try:
                    os.makedirs(os.path.dirname(parsed.output_file))
                except OSError as e:
                    if e.errno != errno.EEXIST:
                        raise
        print(f'[+] Output File: {parsed.output_file}')
        output_file = open(parsed.output_file, 'w')
    
    lang = LANGS.get(parsed.lang, None)
    if not lang:
        print('[+] Language not supported. Supported languages:')
        for language, data in LANGS.items():
            print('[+] {}: {}'.format(language, data['description']))
        exit(0)
    
    print(f'[+] {parsed.lang} selected.')

    try:
        raw_http = ''.join(open(parsed.input_file, 'r').readlines())
    except:
        print('[+] Request file read error.')
        exit(0)
    print('[+] Converting request...')
    request = HTTPRequest(raw_http)
    if request:
        generated = gen(request, lang['template_file'])

        if output_file:
            output_file.write(generated)
            output_file.close()
if __name__ == '__main__':
    main()
