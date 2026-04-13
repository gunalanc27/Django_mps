import json
import os
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.db import transaction
from products.models import Product, Category, Tag

class Command(BaseCommand):
    help = 'Import products from a JSON file'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Path to the JSON file')

    def handle(self, *args, **options):
        json_file = options['json_file']

        if not os.path.exists(json_file):
            self.stdout.write(self.style.ERROR(f'File "{json_file}" does not exist.'))
            return

        with open(json_file, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                self.stdout.write(self.style.ERROR('Invalid JSON format.'))
                return

        if not isinstance(data, list):
            self.stdout.write(self.style.ERROR('JSON data must be a list of products.'))
            return

        self.import_products(data)

    def get_or_create_category_hierarchy(self, category_str):
        """Processes 'Electronics > Laptops' into hierarchical Category objects."""
        if not category_str:
            return None
        
        parts = [p.strip() for p in category_str.split('>')]
        parent = None
        last_cat = None
        
        for part in parts:
            slug = slugify(part)
            cat, created = Category.objects.get_or_create(
                slug=slug,
                defaults={'name': part, 'parent': parent}
            )
            parent = cat
            last_cat = cat
            
        return last_cat

    @transaction.atomic
    def import_products(self, products_data):
        count = 0
        for item in products_data:
            try:
                # 1. Handle Category
                category_name = item.get('category')
                product_category = self.get_or_create_category_hierarchy(category_name)

                # 2. Get or Create Product
                sku = item.get('sku')
                slug = item.get('slug') or slugify(item.get('name'))
                
                # We prioritize SKU for matching, then Slug
                lookup_field = {'sku': sku} if sku else {'slug': slug}
                
                product, created = Product.objects.update_or_create(
                    **lookup_field,
                    defaults={
                        'name': item.get('name'),
                        'slug': slug,
                        'brand': item.get('brand') or '',
                        'model_number': item.get('model_number') or '',
                        'short_description': item.get('short_description') or '',
                        'long_description': item.get('long_description') or '',
                        'price': item.get('price'),
                        'original_price': item.get('original_price'),
                        'currency': item.get('currency', 'INR'),
                        'stock_quantity': item.get('stock_quantity', 0),
                        'availability_status': item.get('availability_status', 'In Stock'),
                        'category': product_category,
                        'video_url': item.get('video_url', ''),
                        'specifications': item.get('specifications', {}),
                        'image_gallery': item.get('image_gallery', []),
                        'is_active': item.get('is_active', True),
                    }
                )

                # 3. Handle Main Image if not set
                if not product.image and item.get('image_gallery'):
                    first_img = item.get('image_gallery')[0]
                    # Assuming the image is in media/products/
                    product.image = f'products/{first_img}'
                    product.save()

                # 4. Handle Tags
                tags_list = item.get('tags', [])
                if tags_list:
                    tag_objs = []
                    for t_name in tags_list:
                        t_slug = slugify(t_name)
                        tag, _ = Tag.objects.get_or_create(slug=t_slug, defaults={'name': t_name})
                        tag_objs.append(tag)
                    product.tags.set(tag_objs)

                count += 1
                action = "Created" if created else "Updated"
                self.stdout.write(self.style.SUCCESS(f'{action} product: {product.name}'))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error importing {item.get("name")}: {str(e)}'))

        self.stdout.write(self.style.SUCCESS(f'Successfully imported {count} products.'))
