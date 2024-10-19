# Blog Content Generator with FTP Image Upload

This Python-based tool provides a graphical interface to help users easily create and manage blog content. It allows you to generate well-structured HTML with SEO features and securely upload images to an FTP server. Ideal for bloggers or content creators who want a quick and easy way to prepare blog content.

## Installation

Simply copy the `blog_generator.py` file to your desired location and edit the configuration as needed.

## Configuration

Update the `CONFIG` dictionary in the script with your FTP credentials and directory path:
```python
CONFIG = {
    "ftp_server": "INSERT YOUR FTP SERVER",
    "ftp_user": "INSERT YOUR FTP USER",
    "ftp_pass": "INSERT YOUR FTP PASSWORD",
    "ftp_directory": "INSERT YOUR FTP DIRECTORY"
}
```
Also, update the expected fingerprint of the FTP server's SSL certificate:
```python
EXPECTED_FINGERPRINT = "INSERT FINGERPRINT HERE FOR FTP"
```

## Usage

1. **Start the Application**:
   ```sh
   python blog_generator.py
   ```

2. **Create Blog Content**:
   - Use the provided GUI to enter blog content.
   - Use tags like `@H1`, `@H2`, `@P`, `@IMGx` to format the text.

3. **Upload Images**:
   - Click the buttons labeled "Bild 1 hochladen", "Bild 2 hochladen", or "Bild 3 hochladen" to select images for upload.
   - The uploaded image URLs will be automatically embedded in the HTML content.

4. **Generate HTML**:
   - Click "Blog generieren" to create the HTML for your blog post.
   - You can then copy the generated HTML to your clipboard for easy use.

## Example Blog Content Markup

- `@H1:` Main header for the blog post.
- `@H2:` Subheaders for sections.
- `@P:` Paragraphs of text.
- `@B:` and `@BEND:` to denote bold text.
- `@A:` to add links (`@A: Link text|https://example.com`).
- `@IMG1`, `@IMG2`, `@IMG3`: To embed images.
- `@IMGx-ALT:` for specifying SEO-friendly alt text for each image.

## Screenshot

![Screenshot](screenshot.png)

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.

## Contributions

Feel free to fork the repository and submit pull requests. Contributions are welcome!

## Issues

If there issues u have to be creative and solve them ;) 
