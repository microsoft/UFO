"""测试pywinauto的能力"""
import control

from typing import List

from PIL import Image, ImageDraw, ImageFont, ImageGrab
from pywinauto.application import Application
from pywinauto.win32structures import RECT


ANNOTATION_COLORS= {
        "Button": "#FFF68F",
        "Edit": "#A5F0B5",
        "TabItem": "#A5E7F0",
        "Document": "#FFD18A",
        "ListItem": "#D9C3FE",
        "MenuItem": "#E7FEC3",
        "ScrollBar": "#FEC3F8",
        "TreeItem": "#D6D6D6",
        "Hyperlink": "#91FFEB",
        "ComboBox": "#D8B6D4"
    }

CONTROL_TYPE_LIST = ["Button", "Edit", "TabItem", "Document", "ListItem", "MenuItem", "ScrollBar", "TreeItem", "Hyperlink", "ComboBox", "RadioButton"]


def coordinate_adjusted(window_rect:RECT, control_rect:RECT):
    """
    Adjust the coordinates of the control rectangle to the window rectangle.
    :param window_rect: The window rectangle.
    :param control_rect: The control rectangle.
    :return: The adjusted control rectangle.
    """
    # (left, top, right, bottom)
    adjusted_rect = (control_rect.left - window_rect.left, control_rect.top - window_rect.top, 
                         control_rect.right - window_rect.left, control_rect.bottom - window_rect.top)
    
    return adjusted_rect

def draw_rectangles_controls(image, coordinate:tuple, label_text:str, botton_margin:int=5, border_width:int=2, font_size:int=25, 
                             font_color:str="#000000", border_color:str="#FF0000", button_color:str="#FFF68F"):
    """
    Draw a rectangle around the control and label it.
    :param image: The image to draw on.
    :param save_path: The path to save the screenshot.
    :param coordinate: The coordinate of the control.
    :param label_text: The text label of the control.
    :param botton_margin: The margin of the button.
    :param border_width: The width of the border.
    :param font_size: The size of the font.
    :param font_color: The color of the font.
    :param border_color: The color of the border.
    :param button_color: The color of the button.
    return: The image with the rectangle and label.
    """
    _ = ImageDraw.Draw(image)
    font = ImageFont.truetype("arial.ttf", font_size) 
    text_size = font.getbbox(label_text)
    
    # set button size + margins
    button_size = (text_size[2]+botton_margin, text_size[3]+botton_margin)
    # create image with correct size and black background
    button_img = Image.new('RGBA', button_size, button_color)
    button_draw = ImageDraw.Draw(button_img)
    button_draw.text((botton_margin/2, botton_margin/2), label_text, font=font, fill=font_color)

    # draw red rectangle around button
    ImageDraw.Draw(button_img).rectangle(
        [(0, 0), (button_size[0] - 1, button_size[1] - 1)],
        outline=border_color, width=border_width
    )
    
    # put button on source image
    image.paste(button_img, (coordinate[0], coordinate[1]))
    return image

def control_annotations(window:str, screenshot_save_path:str, annotated_screenshot_save_path:str, control_list:List, anntation_type:str="number", 
                        color_diff:bool=True, color_default:str="#FFF68F", is_save:bool=True):

    """
    Annotate the controls of the window.
    :param window_title: The title of the window.
    :param screenshot_save_path: The path to save the screenshot.
    :param annotated_screenshot_save_path: The path to save the annotated screenshot.
    :param control_list: The list of the controls to annotate.
    :param anntation_type: The type of the annotation, must be number or letter.
    :param color_diff: Whether to use color difference to annotate different control type.
    :param color_default: The default color of the annotation.
    :param is_save: Whether to save the screenshot and annotated screenshot.
    :return: The dictionary of the annotations and the annotated screenshot.
    """

    annotation_dict = {}
    window_rect = window.rectangle()
    screenshot = window.capture_as_image()
    screenshot_annotated = screenshot.copy()

    assert anntation_type in ["number", "letter"], "The annotation type must be number or letter."

    color_dict = ANNOTATION_COLORS
    for i, control in enumerate(control_list):
        control_rect = control.rectangle()
        adjusted_rect = coordinate_adjusted(window_rect, control_rect)
        adjusted_coordinate = (adjusted_rect[0], adjusted_rect[1])

        if anntation_type == "number":
            label_text = str(i+1)
            screenshot_annotated = draw_rectangles_controls(screenshot_annotated, adjusted_coordinate, label_text, button_color=color_dict.get(control.element_info.control_type, color_default) if color_diff else color_default)
        annotation_dict[label_text] = control

    if is_save:
        screenshot.save(screenshot_save_path)
        screenshot_annotated.save(annotated_screenshot_save_path)
    return annotation_dict, screenshot, screenshot_annotated



if __name__ == "__main__":
    import time
    from datetime import datetime
    import json
    # get all visible app in windows
    desktop_windows_dict, desktop_windows_info = control.get_desktop_app_info_dict()
    print(desktop_windows_dict)
    print('------------------------')
    print(desktop_windows_info)
    # choose a label of app
    app_label = input("Input the label of app:")
    app_window = desktop_windows_dict[app_label]
    # get the root of the app (exe)
    app_root = control.get_application_name(app_window) 
    print(app_root)
    # maximize the app window and focus on it
    app_window.set_focus()
    # find all the control elements in this app
    depth = 0
    while depth != -1:
        depth = int(input("input the depth of the control elements:"))
        time.sleep(5)
        control_list = control.find_control_elements_in_descendants(app_window, CONTROL_TYPE_LIST,depth=depth)
        parent_info ={str(cs):str(control.get_parent_control(cs))  for cs in control_list}  
        descendants_info ={str(cs):[str(csons) for csons in control.get_child_controls(cs)]  for cs in control_list}     

        time_info = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        screenshot_save_path = f"D:/agents/UFO/logs/test_windows/screenshot_{time_info}_{depth}.png"
        annotated_screenshot_save_path = f"D:/agents/UFO/logs/test_windows/screenshot_{time_info}_{depth}_annotated.png"
        annotation_dict, _, _ = control_annotations(app_window, screenshot_save_path, annotated_screenshot_save_path, control_list, anntation_type="number")
        # transfer every value to string in dict
        annotation_dict = {k:str(v) for k,v in annotation_dict.items()}
        with open(screenshot_save_path.replace(".png", ".json"), "w") as f:
            f.writelines(json.dumps(annotation_dict))
        with open(screenshot_save_path.replace(".png", "_parent.json"), "w") as f:
            f.writelines(json.dumps(parent_info))
        with open(screenshot_save_path.replace(".png", "_descendants.json"), "w") as f:
            f.writelines(json.dumps(descendants_info))
    print("finish")