from resources.base import BaseResource

resource = BaseResource('products', stringify_fields=['_id', 'userId', 'categoryId'])
get_items = resource.get_items
get_item = resource.get_item
create_item = resource.create_item
update_item = resource.update_item
delete_item = resource.delete_item
