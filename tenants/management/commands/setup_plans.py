from django.core.management.base import BaseCommand
from tenants.models import SubscriptionPlan


class Command(BaseCommand):
    help = 'Setup initial subscription plans'

    def handle(self, *args, **options):
        plans = [
            {
                'name': 'free',
                'display_name': 'ফ্রি',
                'price_monthly': 0,
                'price_yearly': 0,
                'max_products': 50,
                'max_users': 1,
                'max_monthly_sales': 100,
                'has_reports': True,
                'has_barcode': False,
                'has_api_access': False,
            },
            {
                'name': 'basic',
                'display_name': 'বেসিক',
                'price_monthly': 499,
                'price_yearly': 4990,
                'max_products': 500,
                'max_users': 5,
                'max_monthly_sales': 1000,
                'has_reports': True,
                'has_barcode': True,
                'has_api_access': False,
            },
            {
                'name': 'premium',
                'display_name': 'প্রিমিয়াম',
                'price_monthly': 999,
                'price_yearly': 9990,
                'max_products': 99999,
                'max_users': 20,
                'max_monthly_sales': 99999,
                'has_reports': True,
                'has_barcode': True,
                'has_api_access': True,
            },
        ]
        
        for plan_data in plans:
            plan, created = SubscriptionPlan.objects.get_or_create(
                name=plan_data['name'],
                defaults=plan_data
            )
            if created:
                print(f'Created plan: {plan.name}')
            else:
                print(f'Plan exists: {plan.name}')
        
        print('Done!')
