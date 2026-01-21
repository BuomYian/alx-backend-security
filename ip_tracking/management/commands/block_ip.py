"""
Management command to block IP addresses.

Usage:
    python manage.py block_ip <ip_address> [--reason "reason text"]
    python manage.py block_ip --unblock <ip_address>
    python manage.py block_ip --list
"""

from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError
from ip_tracking.models import BlockedIP


class Command(BaseCommand):
    """Management command to manage blocked IP addresses."""

    help = 'Manage blocked IP addresses'

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            'ip_address',
            nargs='?',
            type=str,
            help='IP address to block or unblock'
        )
        parser.add_argument(
            '--reason',
            type=str,
            default='',
            help='Reason for blocking the IP address'
        )
        parser.add_argument(
            '--unblock',
            action='store_true',
            help='Unblock an IP address'
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='List all blocked IP addresses'
        )

    def handle(self, *args, **options):
        """Execute the command."""
        # List blocked IPs
        if options['list']:
            self.list_blocked_ips()
            return

        # Require IP address for block/unblock operations
        ip_address = options.get('ip_address')
        if not ip_address:
            raise CommandError(
                'IP address is required for block/unblock operations')

        # Unblock an IP
        if options['unblock']:
            self.unblock_ip(ip_address)
        # Block an IP
        else:
            reason = options.get('reason', '')
            self.block_ip(ip_address, reason)

    def block_ip(self, ip_address, reason=''):
        """Block an IP address."""
        try:
            blocked_ip, created = BlockedIP.objects.get_or_create(
                ip_address=ip_address,
                defaults={'reason': reason}
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Successfully blocked IP: {ip_address}'
                    )
                )
                if reason:
                    self.stdout.write(f'  Reason: {reason}')
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠ IP {ip_address} is already blocked'
                    )
                )
                if reason and blocked_ip.reason != reason:
                    blocked_ip.reason = reason
                    blocked_ip.save()
                    self.stdout.write(f'  Reason updated: {reason}')

        except ValidationError as e:
            raise CommandError(f'Invalid IP address: {str(e)}')
        except Exception as e:
            raise CommandError(f'Error blocking IP: {str(e)}')

    def unblock_ip(self, ip_address):
        """Unblock an IP address."""
        try:
            blocked_ip = BlockedIP.objects.get(ip_address=ip_address)
            blocked_ip.delete()
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Successfully unblocked IP: {ip_address}'
                )
            )
        except BlockedIP.DoesNotExist:
            raise CommandError(f'IP {ip_address} is not in the blacklist')
        except Exception as e:
            raise CommandError(f'Error unblocking IP: {str(e)}')

    def list_blocked_ips(self):
        """List all blocked IP addresses."""
        blocked_ips = BlockedIP.objects.all().order_by('-blocked_at')

        if not blocked_ips.exists():
            self.stdout.write(
                self.style.WARNING('No blocked IP addresses found')
            )
            return

        self.stdout.write(
            self.style.SUCCESS(f'\n{blocked_ips.count()} blocked IP(s):\n')
        )

        for blocked_ip in blocked_ips:
            self.stdout.write(
                f'  • {blocked_ip.ip_address} '
                f'(blocked: {blocked_ip.blocked_at.strftime("%Y-%m-%d %H:%M:%S")})'
            )
            if blocked_ip.reason:
                self.stdout.write(f'    Reason: {blocked_ip.reason}')

        self.stdout.write('')
