from django.core.management.base import BaseCommand
from accounts.models import User
from products.models import Category, GSMType, PaperSize, Unit


class Command(BaseCommand):
    help = 'Setup initial data for the Stationery Shop'

    def handle(self, *args, **options):
        # Create superuser if not exists
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@stationery.com',
                password='admin123',
                role='admin',
                first_name='অ্যাডমিন',
            )
            self.stdout.write(self.style.SUCCESS('Superuser "admin" created with password "admin123"'))
        
        # Categories
        categories = [
            'A4 সাইজ কাগজ',
            'A3 সাইজ কাগজ',
            'লিগ্যাল সাইজ কাগজ',
            'অফসেট কাগজ',
            'প্রিন্টিং কাগজ',
            'ফটোকপি কাগজ',
            'আর্ট পেপার',
            'আর্ট কার্ড',
            'ক্রাফট পেপার',
            'কালার পেপার',
            'চার্ট পেপার',
            'পোস্টার পেপার',
            'গ্লসি পেপার',
            'ম্যাট পেপার',
            'ট্রেসিং পেপার',
            'কার্বন পেপার',
            'বন্ড পেপার',
            'স্টিকার পেপার',
            'ফটো পেপার',
            'ব্রাউন পেপার',
            'টিস্যু পেপার',
            'খাতা তৈরির কাগজ',
            'ড্রইং পেপার',
            'গ্রাফ পেপার',
            'লেমিনেটিং শিট',
            'নোট প্যাড কাগজ',
            'থার্মাল পেপার',
        ]
        
        for name in categories:
            Category.objects.get_or_create(name=name)
        self.stdout.write(self.style.SUCCESS(f'{len(categories)} categories created'))
        
        # GSM Types
        gsm_values = [50, 60, 70, 80, 100, 120, 150, 180, 200, 250, 300, 350]
        for gsm in gsm_values:
            GSMType.objects.get_or_create(value=gsm)
        self.stdout.write(self.style.SUCCESS(f'{len(gsm_values)} GSM types created'))
        
        # Paper Sizes
        sizes = [
            ('A4', 210, 297),
            ('A3', 297, 420),
            ('A5', 148, 210),
            ('Legal', 216, 356),
            ('Letter', 216, 279),
            ('F4/Foolscap', 216, 330),
        ]
        for name, w, h in sizes:
            PaperSize.objects.get_or_create(name=name, defaults={'width_mm': w, 'height_mm': h})
        self.stdout.write(self.style.SUCCESS(f'{len(sizes)} paper sizes created'))
        
        # Units
        units = [
            ('রিম', 'রিম'),
            ('পিস', 'পিস'),
            ('প্যাকেট', 'প্যাক'),
            ('বান্ডেল', 'বান্ডে'),
            ('কেজি', 'কেজি'),
            ('শিট', 'শিট'),
        ]
        for name, short in units:
            Unit.objects.get_or_create(name=name, defaults={'short_name': short})
        self.stdout.write(self.style.SUCCESS(f'{len(units)} units created'))
        
        self.stdout.write(self.style.SUCCESS('Initial setup completed!'))
