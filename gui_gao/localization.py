"""English presentation of the existing team service contract.

Use the current team enums for writes and recognize legacy labels for display.
Never translate user-written names or descriptions or migrate stored records.
"""
import re

CATEGORY_TO_WIRE = {
    "Books": "books",
    "Electronics": "electronics",
    "Clothing": "clothing",
    "Home & Living": "household"
}

STATUS_LABELS = {
    "on_sale": "Available",
    "off_sale": "Off sale",
    "\u5728\u552e": "Available",
    "\u5df2\u4e0b\u67b6": "Off sale",
    "\u5df2\u5220\u9664": "Deleted"
}

ERROR_MESSAGES = {
    "Invalid username or password": "Incorrect username or password.",
    "Username already exists": "This username is already taken.",
    "\u7528\u6237\u540d\u6216\u5bc6\u7801\u9519\u8bef": "Incorrect username or password.",
    "\u7528\u6237\u540d\u5df2\u5b58\u5728": "This username is already taken.",
    "\u7528\u6237\u4e0d\u5b58\u5728": "This account does not exist.",
    "\u539f\u5bc6\u7801\u4e0d\u80fd\u4e3a\u7a7a": "Enter your current password.",
    "\u539f\u5bc6\u7801\u9519\u8bef": "The current password is incorrect.",
    "\u5546\u54c1\u4e0d\u5b58\u5728": "This item does not exist.",
    "\u5546\u54c1\u4e0d\u5b58\u5728\u6216\u5df2\u4e0b\u67b6": "This item is unavailable.",
    "\u65e0\u6743\u64cd\u4f5c\u8be5\u5546\u54c1": "You do not have permission to change this item.",
    "\u53d1\u5e03\u8005\u7528\u6237\u4e0d\u5b58\u5728": "The seller account does not exist.",
    "\u5546\u54c1\u5df2\u4e0b\u67b6\uff0c\u65e0\u6cd5\u91cd\u590d\u4e0b\u67b6": "This item is already off sale.",
    "\u5546\u54c1\u5728\u552e\u4e2d\uff0c\u65e0\u9700\u91cd\u65b0\u4e0a\u67b6": "This item is already available.",
    "\u6635\u79f0\u4e0d\u80fd\u4e3a\u7a7a": "Enter a display name.",
    "\u6635\u79f0\u957f\u5ea6\u9700\u4e3a 2-20 \u4e2a\u5b57\u7b26": "Use 2\u201320 characters for the display name.",
    "\u6635\u79f0\u53ea\u80fd\u5305\u542b\u4e2d\u6587\u3001\u82f1\u6587\u3001\u6570\u5b57\u548c\u4e0b\u5212\u7ebf": "Use letters, Chinese characters, digits or underscores for the display name.",
    "\u7528\u6237\u540d\u4e0d\u80fd\u4e3a\u7a7a": "Enter a username.",
    "\u7528\u6237\u540d\u9700\u4e3a 3-20 \u4e2a\u5b57\u7b26\uff0c\u4ee5\u82f1\u6587\u5b57\u6bcd\u5f00\u5934\uff0c\u53ea\u80fd\u5305\u542b\u82f1\u6587\u5b57\u6bcd\u3001\u6570\u5b57\u548c\u4e0b\u5212\u7ebf": "Use 3\u201320 characters, starting with a letter. Letters, digits and underscores only.",
    "\u5bc6\u7801\u4e0d\u80fd\u4e3a\u7a7a": "Enter a password.",
    "\u5bc6\u7801\u9996\u5c3e\u4e0d\u80fd\u5305\u542b\u7a7a\u683c": "Remove leading or trailing spaces from the password.",
    "\u5bc6\u7801\u957f\u5ea6\u9700\u4e3a 8-32 \u4e2a\u5b57\u7b26": "Use 8\u201332 characters for the password.",
    "\u5bc6\u7801\u4e0d\u80fd\u5305\u542b\u7a7a\u683c": "The password cannot contain whitespace.",
    "\u5bc6\u7801\u81f3\u5c11\u5305\u542b\u4e00\u4e2a\u82f1\u6587\u5b57\u6bcd": "The password must include a letter.",
    "\u5bc6\u7801\u81f3\u5c11\u5305\u542b\u4e00\u4e2a\u6570\u5b57": "The password must include a digit.",
    "\u5546\u54c1\u540d\u79f0\u4e0d\u80fd\u4e3a\u7a7a": "Enter an item name.",
    "\u5546\u54c1\u540d\u79f0\u6700\u591a20\u4e2a\u5b57\u7b26": "Item names are limited to 20 characters.",
    "\u5546\u54c1\u540d\u79f0\u6700\u591a 20 \u4e2a\u5b57\u7b26": "Item names are limited to 20 characters.",
    "\u5546\u54c1\u63cf\u8ff0\u4e0d\u80fd\u4e3a\u7a7a": "Enter a description.",
    "\u5546\u54c1\u63cf\u8ff0\u6700\u591a200\u4e2a\u5b57\u7b26": "Descriptions are limited to 200 characters.",
    "\u5546\u54c1\u63cf\u8ff0\u6700\u591a 200 \u4e2a\u5b57\u7b26": "Descriptions are limited to 200 characters.",
    "\u5546\u54c1\u5206\u7c7b\u4e0d\u80fd\u4e3a\u7a7a": "Choose a category.",
    "\u5546\u54c1\u5206\u7c7b\u53ea\u80fd\u662f\uff1a\u4e66\u7c4d\u3001\u7535\u5b50\u4ea7\u54c1\u3001\u670d\u9970\u3001\u751f\u6d3b\u7528\u54c1": "Choose Books, Electronics, Clothing or Home & Living.",
    "\u4ef7\u683c\u5fc5\u987b\u662f\u5927\u4e8e 0 \u7684\u6570\u5b57": "Enter a price greater than zero.",
    "\u4ef7\u683c\u4e0d\u80fd\u4e3a\u7a7a": "Enter a price.",
    "\u4ef7\u683c\u5fc5\u987b\u662f\u6570\u5b57": "Enter a numeric price.",
    "\u4ef7\u683c\u5fc5\u987b\u662f\u6709\u6548\u6570\u5b57": "Enter a finite numeric price.",
    "\u4ef7\u683c\u5fc5\u987b\u5927\u4e8e 0": "Enter a price greater than zero.",
    "\u4ef7\u683c\u6570\u503c\u8d85\u51fa\u5408\u7406\u8303\u56f4": "The price exceeds the supported range.",
    "\u56fe\u7247\u8def\u5f84\u6700\u591a 260 \u4e2a\u5b57\u7b26": "Image paths are limited to 260 characters.",
    "\u7559\u8a00\u4e0d\u80fd\u4e3a\u7a7a": "Enter a comment.",
    "\u64cd\u4f5c\u7c7b\u578b\u4e0d\u80fd\u4e3a\u7a7a": "An activity type is required."
}

ACTION_LABELS = {
    "\u66f4\u65b0\u6635\u79f0": "Update display name",
    "\u66f4\u65b0\u5bc6\u7801": "Update password",
    "\u767b\u5f55": "Sign in",
    "\u53d1\u5e03\u5546\u54c1": "List item",
    "\u7f16\u8f91\u5546\u54c1": "Edit item",
    "\u4e0b\u67b6\u5546\u54c1": "Take item off sale",
    "\u91cd\u65b0\u4e0a\u67b6": "Relist",
    "\u6c38\u4e45\u5220\u9664": "Delete permanently",
    "\u4fee\u6539\u6635\u79f0": "Update display name",
    "\u4fee\u6539\u5bc6\u7801": "Update password",
    "\u53d6\u6d88\u6536\u85cf": "Unsave",
    "\u6536\u85cf\u5546\u54c1": "Save item",
    "\u53d1\u5e03\u7559\u8a00": "Post comment",
    "\u63d0\u4ea4\u8d2d\u4e70\u610f\u5411": "Send enquiry"
}

ERROR_PREFIXES = {
    "\u5546\u54c1\u53d1\u5e03\u5931\u8d25": "Could not list the item. Check file permissions and data files.",
    "\u5546\u54c1\u672a\u5220\u9664": "The item was not deleted because its archive could not be saved.",
    "\u6570\u636e\u6587\u4ef6": "Could not access the data file. Check its contents and permissions.",
    "\u8bfb\u53d6": "Could not read the data file. Check its contents and permissions.",
    "\u5199\u5165": "Could not save the data file. Check file permissions and try again."
}

CATEGORY_LABELS = {value: label for label, value in CATEGORY_TO_WIRE.items()}
CATEGORY_LABELS.update({
    "\u4e66\u7c4d": "Books",
    "\u7535\u5b50\u4ea7\u54c1": "Electronics",
    "\u670d\u9970": "Clothing",
    "\u751f\u6d3b\u7528\u54c1": "Home & Living",
})


def category_to_wire(label):
    return CATEGORY_TO_WIRE.get(label, label)


def present_item(item):
    """Return a display copy, leaving stored data and user-authored text intact."""
    if not isinstance(item, dict):
        return item
    result = dict(item)
    for field, labels in (("category", CATEGORY_LABELS), ("status", STATUS_LABELS)):
        if field in result:
            result[field] = labels.get(result[field], result[field])
    return result


def error_text(message):
    message = str(message)
    if message in ERROR_MESSAGES:
        return ERROR_MESSAGES[message]
    for prefix, english in ERROR_PREFIXES.items():
        if message.startswith(prefix):
            return english
    if re.search(r"[\u3400-\u9fff]", message):
        return "Could not complete the action. Check your input and data files, then try again."
    return message


def present_log(record):
    result = dict(record)
    action = result.get("action_type", "")
    result["action_type"] = ACTION_LABELS.get(action, action)
    # Keep the rest of the detail unchanged: it may contain a user's item title.
    result["detail"] = re.sub(r"^\u5546\u54c1\s*#", "Item #", result.get("detail", ""))
    return result
