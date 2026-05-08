from resources.base import BaseResource

resource = BaseResource('categories', stringify_fields=['_id', 'userId'])
get_items = resource.get_items
get_item = resource.get_item
create_item = resource.create_item
update_item = resource.update_item
delete_item = resource.delete_item
