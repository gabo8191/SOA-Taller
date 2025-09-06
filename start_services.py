#!/usr/bin/env python3
import subprocess
import sys
import time
import signal
from typing import List, Optional


class ServiceManager:


    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.services = [
            {
                'name': 'Students Service',
                'script': 'students_service.py',
                'port': 5001
            },
            {
                'name': 'Courses Service',
                'script': 'courses_service.py',
                'port': 5002
            },
            {
                'name': 'Enrollments Service',
                'script': 'enrollments_service.py',
                'port': 5003
            },
            {
                'name': 'API Gateway',
                'script': 'api_gateway.py',
                'port': 5000
            }
        ]

    def start_service(self, service: dict) -> Optional[subprocess.Popen]:
        print(f"🚀 Starting {service['name']} on port {service['port']}...")

        try:
            process = subprocess.Popen([
                sys.executable, service['script']
            ])

            time.sleep(3)

            if process.poll() is None:
                print(f"✅ {service['name']} started successfully")
                return process
            else:
                print(f"❌ Error starting {service['name']}: Process exited with code {process.returncode}")
                return None

        except Exception as e:
            print(f"❌ Error starting {service['name']}: {str(e)}")
            return None

    def start_all_services(self):
        print("🎓 Starting SOA Academic Information System")
        print("=" * 60)

        for service in self.services:
            process = self.start_service(service)
            if process:
                self.processes.append(process)
            else:
                print(f"⚠️  Could not start {service['name']}")

        if self.processes:
            print(f"\n✨ System started with {len(self.processes)} services")
            self.print_service_urls()
            self.wait_for_shutdown()
        else:
            print("\n❌ Could not start any services")
            sys.exit(1)

    def print_service_urls(self):
        print("\n🌐 Service URLs:")
        print("-" * 40)

        for service in self.services:
            url = f"http://localhost:{service['port']}"
            print(f"   {service['name']:.<25} {url}")

        print(f"\n🖥️  Access the web application at: http://localhost:5000")
        print("📚 API documentation available at each service /health endpoint")

    def wait_for_shutdown(self):
        print("\n⌨️  Press Ctrl+C to stop all services")

        def signal_handler(sig, frame):
            print("\n🛑 Stopping services...")
            self.stop_all_services()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)

        try:
            while True:
                running_processes = []
                for process in self.processes:
                    if process.poll() is None:
                        running_processes.append(process)
                    else:
                        print(f"⚠️  A service stopped unexpectedly")

                self.processes = running_processes

                if not self.processes:
                    print("❌ All services stopped")
                    break

                time.sleep(5)

        except KeyboardInterrupt:
            pass

    def stop_all_services(self):
        for i, process in enumerate(self.processes):
            if process.poll() is None:
                print(f"   Stopping service {i+1}...")
                process.terminate()

                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print(f"   Force stopping service {i+1}...")
                    process.kill()

        print("✅ All services have been stopped")

    def check_dependencies(self) -> bool:
        try:
            import flask
            import flask_cors
            import requests
            print("✅ Dependencies verified")
            print("📦 Using in-memory storage (no database required)")
            return True
        except ImportError as e:
            print(f"❌ Missing dependency: {e}")
            print("   Run: pip install -r requirements.txt")
            return False


def main():
    print("🎓 SOA Academic Information System")
    print("   Service Oriented Architecture with Flask")
    print()

    manager = ServiceManager()

    if not manager.check_dependencies():
        sys.exit(1)

    manager.start_all_services()


if __name__ == '__main__':
    main()
