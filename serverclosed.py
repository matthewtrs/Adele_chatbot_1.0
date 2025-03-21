from http.server import HTTPServer, BaseHTTPRequestHandler

class MaintenanceHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(503)  # Service Unavailable
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        maintenance_message = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Server Maintenance</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    text-align: center;
                    padding-top: 100px;
                    background-color: #f5f5f5;
                }
                .container {
                    background-color: white;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    padding: 40px;
                    max-width: 600px;
                    margin: 0 auto;
                }
                h1 {
                    color: #e74c3c;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Server Under Maintenance</h1>
                <p>Cokkk lagi Update.</p>
                <p>Kalem.</p>
            </div>
        </body>
        </html>
        """
        
        self.wfile.write(maintenance_message.encode())

def run_server(port=5000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, MaintenanceHandler)
    print(f"Server running on port {port}")
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()