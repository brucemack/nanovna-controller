from http.server import BaseHTTPRequestHandler
from urllib import parse
from jinja2 import Template

template_text = """
    <head>
        <title>NanoVNA Control Panel</title>
    </head>
    <body>
        <h1>NanoVNA Control Panel</h1>
        <p>The NanoVNA is connected.</p>
        <form>
            <label for="start_freq">Start Frequency in Megahertz</label>
            <input type="text" id="start_freq"/>
            <label for="end_freq">End Frequency in Megahertz</label>
            <input type="text" id="end_freq"/>
            <label for="step">Step in Megahertz</label>
            <input type="text" id="step"/>
            <button>Sweep</button>
        </form>
        <table>
            <caption>Sweep result</caption>
            <thead>
                <tr>
                    <th>28.300</th>
                    <th>28.310</th>
                    <th>28.320</th>
                    <th>28.330</th>
                    <th>28.340</th>
                    <th>28.350</th>
                    <th>28.360 best match</th>
                    <th>28.370</th>
                    <th>28.380</th>
                    <th>28.390</th>
                    <th>28.400</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>2.10</td>
                    <td>2.05</td>
                    <td>2.00</td>
                    <td>1.75</td>
                    <td>1.70</td>
                    <td>1.50</td>
                    <td>1.30 best match</td>
                    <td>1.35</td>
                    <td>1.55</td>
                    <td>1.70</td>
                    <td>1.80</td>
                </tr>
            </tbody>
        </table>
    </body>
</html>
"""

"""
{% for user in users %}
  <li><a href="{{ user.url }}">{{ user.username }}</a></li>
{% endfor %}
</ul>
    </body>
</html>
"""

class GetHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        parsed_path = parse.urlparse(self.path)
        """
        message_parts = [
            'CLIENT VALUES:',
            'client_address={} ({})'.format(
                self.client_address,
                self.address_string()),
            'command={}'.format(self.command),
            'path={}'.format(self.path),
            'real path={}'.format(parsed_path.path),
            'query={}'.format(parsed_path.query),
            'request_version={}'.format(self.request_version),
            '',
            'SERVER VALUES:',
            'server_version={}'.format(self.server_version),
            'sys_version={}'.format(self.sys_version),
            'protocol_version={}'.format(self.protocol_version),
            '',
            'HEADERS RECEIVED:',
        ]
        for name, value in sorted(self.headers.items()):
            message_parts.append(
                '{}={}'.format(name, value.rstrip())
            )
        message_parts.append('')
        message = '\r\n'.join(message_parts)
        """

        template = Template(template_text)
        users = [{'username': 'test', 'url': 'http://www'}]
        a = {'users': users}
        message = template.render(a)

        self.send_response(200)
        self.send_header('Content-Type',
            'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(message.encode('utf-8'))

listen_host = "localhost"
listen_port = 8080



if __name__ == '__main__':
    from http.server import HTTPServer
    server = HTTPServer((listen_host, listen_port), GetHandler)
    server.serve_forever()
