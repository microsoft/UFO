"""测试win32com的能力"""
import win32com.client as win32

word = win32.gencache.EnsureDispatch('Word.Application')
word.Visible = True  # 显示Word应用
doc = word.Documents.Add()  # 创建一个新文档

doc.Content.Text = "Hello, this is some text."  # 直接添加文本
selection = word.Selection
selection.TypeText("Hello, another line of text.\n")  # 使用光标选择添加文本

# 设置标题
selection.Style = word.ActiveDocument.Styles("Heading 1")
selection.TypeText("This is a Title\n")

# 设置粗体
selection.Font.Bold = True
selection.TypeText("This is bold text\n")

# 设置斜体
selection.Font.Italic = True
selection.TypeText("This is italic text\n")

# 设置下划线
selection.Font.Underline = True
selection.TypeText("This is underlined text\n")

# 设置字体和大小
selection.Font.Name = 'Arial'
selection.Font.Size = 14
selection.TypeText("This is Arial 14\n")

image_path = 'path_to_image.jpg'
selection.InlineShapes.AddPicture(image_path)

num_rows = 3
num_columns = 2
table = doc.Tables.Add(selection.Range, num_rows, num_columns)
for i in range(1, num_rows + 1):
    for j in range(1, num_columns + 1):
        table.Cell(i, j).Range.Text = f"Cell {i},{j}"

doc_path = "path_to_save_document\\document_name.docx"
doc.SaveAs(doc_path)

doc.Close()  # 关闭文档
word.Quit()  # 关闭Word应用
