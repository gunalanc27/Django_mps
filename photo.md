# Fix: Read-Only Filesystem on Vercel (Image Uploads)

## Problem
Vercel's filesystem is read-only. Django's `ImageField` tries to write uploaded files to disk, causing:
```
OSError: [Errno 30] Read-only file system: '/var/task/media/payment_proofs/...'
```

## Solution: Cloudinary Cloud Storage

Use `django-cloudinary-storage` so Django's `ImageField` automatically uploads to Cloudinary instead of local disk. Zero changes to models or forms.

## Proposed Changes

### Dependencies

#### [MODIFY] requirements.txt
- Add `cloudinary==1.42.1`
- Add `django-cloudinary-storage==0.3.0`

---

### Configuration

#### [MODIFY] .env
- Add `CLOUDINARY_URL=cloudinary://API_KEY:API_SECRET@CLOUD_NAME`

#### [MODIFY] tes/settings.py
- Add Cloudinary config block (reads from `CLOUDINARY_URL`)
- Set `DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'`

---

### Google Sheets Sync

#### [MODIFY] orders/views.py
- Update [_push_to_sheets](file:///home/darkemperor/aathi/Web/Python/django_Learn/orders/views.py#14-57) to send `order.payment_screenshot.url` (Cloudinary URL)
  instead of base64-encoding the local file (which no longer exists on disk)

#### Apps Script (manual update required)
- Change `appendRow` column L from a Drive upload to the Cloudinary URL directly
- Use `=IMAGE(url)` formula in the cell so the image is visible in the sheet

## Verification Plan

### Manual Test
1. Deploy to Vercel (after pushing changes)
2. Go to `https://django-mps.vercel.app/orders/checkout/`
3. Add item to cart, complete checkout with a payment screenshot
4. Confirm: no `OSError` — order confirmation page loads
5. Open Google Sheet — new row appears with a clickable image URL in column L
