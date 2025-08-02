from ttkbootstrap import Style
from ttkbootstrap.constants import *
from typing import Dict, Any, Tuple

class AppStyles:
    def __init__(self, theme: str = "morph"):
        self.style = Style(theme=theme)
        self._configure_styles()
        
    def _configure_styles(self) -> None:
        self.style.configure(
            'TFrame',
            background=self.style.colors.bg
        )
        
        self.style.configure(
            'TLabel',
            font=('Helvetica', 10),
            foreground=self.style.colors.fg
        )
        
        self.style.configure(
            'Header.TLabel',
            font=('Helvetica', 18, 'bold'),
            foreground=self.style.colors.primary
        )
        
        self.style.configure(
            'Subheader.TLabel',
            font=('Helvetica', 14),
            foreground=self.style.colors.secondary
        )
        
        self.style.configure(
            'Primary.TButton',
            font=('Helvetica', 10, 'bold'),
            bootstyle=(OUTLINE, PRIMARY)
        )
        
        self.style.configure(
            'Success.TButton',
            font=('Helvetica', 10, 'bold'),
            bootstyle=(OUTLINE, SUCCESS)
        )
        
        self.style.configure(
            'Danger.TButton',
            font=('Helvetica', 10, 'bold'),
            bootstyle=(OUTLINE, DANGER)
        )
        
        self.style.configure(
            'TEntry',
            font=('Helvetica', 10),
            padding=5
        )
        
        self.style.configure(
            'Transaction.Treeview',
            font=('Helvetica', 10),
            rowheight=25,
            fieldbackground=self.style.colors.bg
        )
        
        self.style.configure(
            'Transaction.Treeview.Heading',
            font=('Helvetica', 10, 'bold')
        )
        
        self.style.configure(
            'Account.TLabelframe',
            font=('Helvetica', 12, 'bold'),
            labeloutside=True
        )
        
    def get_style_config(self) -> Dict[str, Any]:
        return {
            'colors': {
                'primary': PRIMARY,
                'secondary': SECONDARY,
                'success': SUCCESS,
                'info': INFO,
                'warning': WARNING,
                'danger': DANGER,
                'bg': self.style.colors.bg,
                'fg': self.style.colors.fg,
                'inputbg': self.style.colors.inputbg
            },
            'fonts': {
                'small': ('Helvetica', 8),
                'normal': ('Helvetica', 10),
                'medium': ('Helvetica', 12),
                'large': ('Helvetica', 14),
                'title': ('Helvetica', 18, 'bold')
            },
            'padding': {
                'small': (3, 3),
                'normal': (5, 5),
                'medium': (10, 10),
                'large': (15, 15)
            },
            'border': {
                'normal': 1,
                'thick': 2
            }
        }
    
    def get_theme(self) -> str:
        return self.style.theme.name
    
    def set_theme(self, theme_name: str) -> None:
        self.style.theme_use(theme_name)
        self._configure_styles()

app_style = AppStyles()

def get_style() -> Style:
    return app_style.style

def get_config() -> Dict[str, Any]:
    return app_style.get_style_config()

def get_padding(size: str = 'normal') -> Tuple[int, int]:
    return app_style.get_style_config()['padding'].get(size, (5, 5))

def get_font(size: str = 'normal') -> Tuple[str, int]:
    return app_style.get_style_config()['fonts'].get(size, ('Helvetica', 10))