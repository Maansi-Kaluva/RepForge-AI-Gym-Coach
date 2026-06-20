import os
import streamlit as st
import streamlit.components.v1 as components
import base64

def load_css(file_path):
    if os.path.exists(file_path):     # for loading css file for styling
        with open(file_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html = True)

def inject_local_font(font_path, font_name):
    if not os.path.exists(font_path):
        return
    
    with open(font_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()

        ext = os.path.splitext(font_path)[1].lstrip(".")      # splits file_name and .otf; [1] -> ".otf"; lstrip(".") -> gives "otf"
        fmt = {"ttf": "truetype"}.get(ext, ext)  # .get(key, default) -> 2 params. If ext ("otf") found in the dict return "opentype", else return "ext" value.
        mime = {"ttf": "font/ttf"}.get(ext, f"font{ext}")   # MIME type tells the browser what kind of file/data something is (like font/otf, image/png, text/html).

        st.markdown(f"""         
                <style>
                @font-face {{
                    font-family: '{font_name}';
                    src: url('data:{mime}; base64,{encoded}') format('{fmt}');
                    font-weight: 100 900;
                    font-style: normal;
                }}
                </style>
            """, unsafe_allow_html = True)         # st.markdown - injects CSS into Streamlit
        
def inject_webrtc_styles():
    font_path = os.path.join(os.getcwd(), "static", "AdobeClean-SemiCn.ttf")
    
    if not os.path.exists(font_path):
        return

    with open(font_path, "rb") as font_file:
        encoded_font = base64.b64encode(font_file.read()).decode()  # encodes the binary font file into Base64 bytes, then .decode() converts those bytes into a normal Python string.

    components.html(  # Injects raw HTML + JS into Streamlit app. Normally Streamlit hides direct HTML access. This bypasses that. JavaScript starts. Everything below runs in browser, NOT Python.
        f"""
        <script>        
        (function patchWebRTCStyles() {{        
            function injectIntoIframe(iframe) {{
                try {{
                    const doc = iframe.contentDocument || iframe.contentWindow.document;
                    if (!doc || !doc.head) return;
                    if (doc.head.querySelector('#webrtc-custom-styles')) return;
                    const style = doc.createElement('style');
                    style.id = 'webrtc-custom-styles';
                    style.textContent = `
                        @font-face {{
                            font-family: 'AdobeClean';
                            src: url('data:font/ttf;base64,{encoded_font}') format('truetype');
                            font-weight: 100 900;
                            font-style: normal;
                        }}
                        .MuiButtonBase-root,
                        .MuiButton-root,
                        .MuiButton-contained,
                        .MuiButton-text {{
                            border-radius: 0 !important;
                            font-family: 'AdobeClean', sans-serif !important;
                            letter-spacing: 0.05em !important;
                        }}
                    `;
                    doc.head.appendChild(style);
                }} catch (e) {{
                    console.warn('[patcher] could not inject:', e);
                }}
            }}

            function findAndPatch() {{
                const parentDoc = window.parent.document;
                const iframes = parentDoc.querySelectorAll('iframe');
                iframes.forEach(iframe => {{
                    if (iframe.src && iframe.src.includes('webrtc')) {{
                        if (iframe.contentDocument && iframe.contentDocument.readyState === 'complete') {{
                            injectIntoIframe(iframe);
                        }} else {{
                            iframe.addEventListener('load', () => injectIntoIframe(iframe));
                        }}
                    }}
                }});    
            }}

            findAndPatch();
            setInterval(findAndPatch, 1000);
        }})();
        </script>
        """,
        height=0,
    )        

# Big picture:
# Python -> Inject JS Script -> JS enters iframe -> Adds custom CSS there
