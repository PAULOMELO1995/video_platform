import sys
import os
import cv2
import numpy as np
import re
import time
import json
import random
import urllib.request
import urllib.parse
import socket
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTextEdit, QSlider, QFileDialog, QMessageBox, 
                             QGroupBox, QProgressBar, QComboBox, QDialog, 
                             QDialogButtonBox, QCheckBox, QFrame, QRadioButton,
                             QButtonGroup, QTabWidget)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QImage, QPixmap, QIcon, QFont, QPalette, QColor
import requests

# Verifica e instala dependências se necessário
try:
    import yt_dlp
except ImportError:
    print("Instalando yt-dlp...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp"])
    import yt_dlp

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Instalando BeautifulSoup...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "beautifulsoup4"])
    from bs4 import BeautifulSoup

class DerrubarRestricao(QThread):
    """
    Classe especializada em derrubar restrições de vídeos
    """
    progresso = pyqtSignal(int)
    status = pyqtSignal(str)
    resultado = pyqtSignal(str, bool)  # mensagem, sucesso
    video_encontrado = pyqtSignal(str)  # URL do vídeo encontrado

    def __init__(self, url, tipo_restricao=None, derrubar_ativa=True):
        super().__init__()
        self.url = url
        self.tipo_restricao = tipo_restricao
        self.derrubar_ativa = derrubar_ativa
        self.video_url = None

    def run(self):
        try:
            self.status.emit("Analisando restrições...")
            
            # Se não foi especificado o tipo de restrição, detecta automaticamente
            if not self.tipo_restricao:
                self.tipo_restricao = self._detectar_tipo_restricao()
                self.status.emit(f"Restrição detectada: {self.tipo_restricao}")

            # Se a derrubada está ativada, tenta métodos específicos
            if self.derrubar_ativa:
                self._aplicar_metodos_derrubada()
            else:
                # Apenas análise sem derrubar
                self.status.emit("Modo análise: restrições não serão derrubadas")
                self.video_url = self._buscar_url_video()
                
            if self.video_url:
                self.video_encontrado.emit(self.video_url)
                self.resultado.emit("URL do vídeo encontrada com sucesso!", True)
            else:
                self.resultado.emit("Não foi possível encontrar o URL do vídeo.", False)

        except Exception as e:
            self.resultado.emit(f"Erro: {str(e)}", False)

    def _detectar_tipo_restricao(self):
        """Detecta automaticamente o tipo de restrição"""
        url = self.url.lower()
        
        if any(x in url for x in ['age_verification', 'age_check', 'verify_age']):
            return "verificacao_idade"
        elif any(x in url for x in ['restricted', 'restrito', 'bloqueado']):
            return "conteudo_restringido"
        elif any(x in url for x in ['region', 'country', 'pais', 'regiao']):
            return "restricao_regional"
        elif any(x in url for x in ['login', 'signin', 'entrar', 'acesso']):
            return "login_obrigatorio"
        elif any(x in url for x in ['private', 'privado', 'particular']):
            return "video_privado"
        elif any(x in url for x in ['token', 'key', 'chave', 'access_key']):
            return "acesso_por_token"
        else:
            return "restricao_desconhecida"

    def _aplicar_metodos_derrubada(self):
        """Aplica métodos específicos baseados no tipo de restrição"""
        metodos = {
            "verificacao_idade": self._derrubar_verificacao_idade,
            "restricao_regional": self._derrubar_restricao_regional,
            "login_obrigatorio": self._derrubar_login_obrigatorio,
            "video_privado": self._derrubar_video_privado,
            "acesso_por_token": self._derrubar_acesso_token,
            "conteudo_restringido": self._derrubar_conteudo_restringido,
            "restricao_desconhecida": self._derrubar_generico
        }

        metodo = metodos.get(self.tipo_restricao, self._derrubar_generico)
        self.video_url = metodo()

    def _derrubar_verificacao_idade(self):
        """Métodos para derrubar verificação de idade"""
        self.status.emit("Contornando verificação de idade...")
        
        # Método 1: Headers que simulam maior idade
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'X-Forwarded-For': '192.168.1.1',
            'Referer': 'https://www.google.com/', 
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        
        return self._buscar_com_headers(headers)

    def _derrubar_restricao_regional(self):
        """Métodos para derrubar restrições regionals"""
        self.status.emit("Contornando restrição regional...")
        
        # Método 1: Headers que simulam outro país
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'en-US,en;q=0.5',
            'X-Forwarded-For': '8.8.8.8',
        }
        
        return self._buscar_com_headers(headers)

    def _derrubar_login_obrigatorio(self):
        """Métodos para contornar necessidade de login"""
        self.status.emit("Contornando exigência de login...")
        
        # Tenta acessar versão mobile ou embed
        url_modificada = self.url.replace('www.', 'm.').replace('/watch?v=', '/embed/')
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36',
            'Referer': 'https://www.google.com/',
        }
        
        return self._buscar_url_recursivo(url_modificada, headers)

    def _derrubar_video_privado(self):
        """Métodos para acessar vídeos privados"""
        self.status.emit("Tentando acessar vídeo privado...")
        return self._buscar_url_video()

    def _derrubar_acesso_token(self):
        """Métodos para contornar acesso por token"""
        self.status.emit("Contornando restrição por token...")
        
        # Tenta extrair token da URL ou gerar um
        parsed = urlparse(self.url)
        query_params = parse_qs(parsed.query)
        
        # Adiciona parâmetros comuns de token
        query_params['access_token'] = ['fake_token_12345']
        query_params['key'] = ['abc123def456']
        query_params['token'] = ['bypass_restriction']
        
        new_query = urlencode(query_params, doseq=True)
        new_url = urlunparse(parsed._replace(query=new_query))
        
        return self._buscar_url_recursivo(new_url)

    def _derrubar_conteudo_restringido(self):
        """Métodos para conteúdo restrito"""
        self.status.emit("Contornando conteúdo restrito...")
        return self._buscar_url_video()

    def _derrubar_generico(self):
        """Métodos genéricos para qualquer restrição"""
        self.status.emit("Aplicando métodos genéricos...")
        
        # Tenta várias estratégias
        estrategias = [
            self._buscar_url_video,
            lambda: self._buscar_com_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.google.com/',
                'X-Requested-With': 'XMLHttpRequest'
            }),
            self._buscar_em_servidores_externos
        ]
        
        for estrategia in estrategias:
            try:
                resultado = estrategia()
                if resultado:
                    return resultado
            except:
                continue
        
        return None

    def _buscar_url_video(self):
        """Busca URL do vídeo na página"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
            
            response = requests.get(self.url, headers=headers, timeout=15)
            return self._extrair_url_video(response.text)
        except Exception as e:
            self.status.emit(f"Erro ao buscar URL: {str(e)}")
            return None

    def _buscar_com_headers(self, headers):
        """Busca URL do vídeo com headers personalizados"""
        try:
            response = requests.get(self.url, headers=headers, timeout=15)
            return self._extrair_url_video(response.text)
        except Exception as e:
            self.status.emit(f"Erro com headers personalizados: {str(e)}")
            return None

    def _buscar_url_recursivo(self, url, headers=None):
        """Busca recursivamente por URL de vídeo"""
        try:
            if headers is None:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            
            response = requests.get(url, headers=headers, timeout=15)
            return self._extrair_url_video(response.text)
        except:
            return None

    def _buscar_em_servidores_externos(self):
        """Busca o vídeo em servidores externos de espelhamento"""
        try:
            # Servidores que espelham conteúdo
            servidores = [
                f'https://9xbuddy.in/process?url={self.url}',
                f'https://en.savefrom.net/1/?url={self.url}',
            ]
            
            for servidor in servidores:
                try:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                    response = requests.get(servidor, headers=headers, timeout=10)
                    video_url = self._extrair_url_video(response.text)
                    if video_url:
                        return video_url
                except:
                    continue
            return None
        except:
            return None

    def _extrair_url_video(self, html_content):
        """Extrai URL de vídeo do conteúdo HTML"""
        try:
            # Padrões comuns para URLs de vídeo
            patterns = [
                r'src="([^"]+\.mp4[^"]*)"',
                r'source src="([^"]+)"',
                r'video_url=["\']([^"\']+)["\']',
                r'file: ["\']([^"\']+)["\']',
                r'(https?://[^\"\s<>]+\.(mp4|webm|m3u8))',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                for match in matches:
                    video_url = match[0] if isinstance(match, tuple) else match
                    
                    # Verifica se é uma URL válida
                    if video_url and self._is_valid_video_url(video_url):
                        # Conserta URL se necessário
                        if video_url.startswith('//'):
                            video_url = 'https:' + video_url
                        elif video_url.startswith('/'):
                            parsed = urlparse(self.url)
                            video_url = f"{parsed.scheme}://{parsed.netloc}{video_url}"
                        
                        self.status.emit(f"URL de vídeo encontrada: {video_url}")
                        return video_url
            
            return None
        except Exception as e:
            self.status.emit(f"Erro ao extrair URL: {str(e)}")
            return None

    def _is_valid_video_url(self, url):
        """Verifica se é uma URL de vídeo válida"""
        video_extensions = ['.mp4', '.webm', '.m3u8', '.mkv', '.avi', '.flv', '.mov']
        return any(url.lower().endswith(ext) for ext in video_extensions)

    def url_video(self):
        """Retorna a URL do vídeo encontrada"""
        return self.video_url

class RestricaoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurações de Restrição")
        self.setModal(True)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Tipo de restrição
        tipo_group = QGroupBox("Tipo de Restrição")
        tipo_layout = QVBoxLayout(tipo_group)
        
        self.tipos = {
            "Auto-detect": "auto",
            "Verificação de Idade": "verificacao_idade",
            "Restrição Regional": "restricao_regional", 
            "Login Obrigatório": "login_obrigatorio",
            "Vídeo Privado": "video_privado",
            "Acesso por Token": "acesso_por_token",
            "Conteúdo Restrito": "conteudo_restringido"
        }
        
        self.tipo_combo = QComboBox()
        for nome, valor in self.tipos.items():
            self.tipo_combo.addItem(nome, valor)
        tipo_layout.addWidget(self.tipo_combo)
        
        # Opção de derrubar
        derrubar_group = QGroupBox("Opções")
        derrubar_layout = QVBoxLayout(derrubar_group)
        
        self.derrubar_sim = QRadioButton("Sim, tentar derrubar restrições")
        self.derrubar_nao = QRadioButton("Não, apenas analisar")
        self.derrubar_sim.setChecked(True)
        
        derrubar_layout.addWidget(self.derrubar_sim)
        derrubar_layout.addWidget(self.derrubar_nao)
        
        # Botões
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(tipo_group)
        layout.addWidget(derrubar_group)
        layout.addWidget(button_box)
        
    def get_config(self):
        return {
            'tipo_restricao': self.tipo_combo.currentData(),
            'derrubar_ativa': self.derrubar_sim.isChecked()
        }

class VideoDownloader(QThread):
    progress_updated = pyqtSignal(int)
    download_finished = pyqtSignal(str)
    info_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    status_message = pyqtSignal(str)

    def __init__(self, url, options=None):
        super().__init__()
        self.url = url
        self.options = options or {}
        self.output_path = "downloads"
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)

    def run(self):
        try:
            # Configurações padrão para yt-dlp
            default_opts = {
                'quiet': True,
                'no_warnings': False,
                'outtmpl': os.path.join(self.output_path, '%(title)s.%(ext)s'),
                'progress_hooks': [self.progress_hook],
                'format': 'best[height<=720]',
            }
            
            # Mescla com opções personalizadas
            ydl_opts = {**default_opts, **self.options}
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Obtém informações do vídeo
                self.status_message.emit("Obtendo informações do vídeo...")
                info = ydl.extract_info(self.url, download=False)
                self.info_ready.emit(info)
                
                # Faz o download
                self.status_message.emit("Iniciando download...")
                ydl.download([self.url])
                
                # Encontra o arquivo baixado
                filename = ydl.prepare_filename(info)
                if os.path.exists(filename):
                    self.download_finished.emit(filename)
                else:
                    # Tenta encontrar o arquivo com extensão diferente
                    base_name = os.path.splitext(filename)[0]
                    for ext in ['.mp4', '.webm', '.mkv', '.avi', '.flv']:
                        if os.path.exists(base_name + ext):
                            self.download_finished.emit(base_name + ext)
                            return
                    self.error_occurred.emit("Arquivo baixado não encontrado")
                    
        except Exception as e:
            self.error_occurred.emit(f"Erro no download: {str(e)}")

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            if d.get('total_bytes'):
                percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
            elif d.get('total_bytes_estimate'):
                percent = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 100
            else:
                percent = 0
            self.progress_updated.emit(int(percent))
            self.status_message.emit(f"Baixando: {int(percent)}%")

class ComplexVideoDownloader(QThread):
    progress_updated = pyqtSignal(int)
    download_finished = pyqtSignal(str)
    info_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    status_message = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url
        self.output_path = "downloads"
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)

    def run(self):
        try:
            # Tenta diferentes estratégias para URLs complexas
            strategies = [
                self._try_standard_download,
                self._try_with_custom_headers,
                self._try_proxy_access,
                self._try_direct_link_extraction,
            ]
            
            for i, strategy in enumerate(strategies):
                self.status_message.emit(f"Tentativa {i+1}/{len(strategies)}")
                success = strategy()
                if success:
                    return
                    
            self.error_occurred.emit("Todas as estratégias falharam")
            
        except Exception as e:
            self.error_occurred.emit(f"Erro no download complexo: {str(e)}")

    def _try_standard_download(self):
        """Tenta download padrão com yt-dlp"""
        try:
            ydl_opts = {
                'quiet': True,
                'outtmpl': os.path.join(self.output_path, '%(title)s.%(ext)s'),
                'progress_hooks': [self.progress_hook],
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=False)
                self.info_ready.emit(info)
                ydl.download([self.url])
                
                filename = ydl.prepare_filename(info)
                if os.path.exists(filename):
                    self.download_finished.emit(filename)
                    return True
            return False
        except:
            return False

    def _try_with_custom_headers(self):
        """Tenta com headers personalizados"""
        try:
            ydl_opts = {
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Referer': 'https://www.google.com/',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                },
                'outtmpl': os.path.join(self.output_path, '%(title)s.%(ext)s'),
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=False)
                self.info_ready.emit(info)
                ydl.download([self.url])
                
                filename = ydl.prepare_filename(info)
                if os.path.exists(filename):
                    self.download_finished.emit(filename)
                    return True
            return False
        except:
            return False

    def _try_proxy_access(self):
        """Tenta usar proxy"""
        try:
            # Lista de proxies públicos (usar com cautela)
            proxies = [
                None,  # Sem proxy primeiro
            ]
            
            for proxy in proxies:
                try:
                    ydl_opts = {
                        'proxy': proxy,
                        'outtmpl': os.path.join(self.output_path, '%(title)s.%(ext)s'),
                    }
                    
                    if proxy:
                        self.status_message.emit(f"Tentando com proxy: {proxy}")
                    
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(self.url, download=False)
                        ydl.download([self.url])
                        
                        filename = ydl.prepare_filename(info)
                        if os.path.exists(filename):
                            self.download_finished.emit(filename)
                            return True
                except:
                    continue
            return False
        except:
            return False

    def _try_direct_link_extraction(self):
        """Tenta extrair link direto do vídeo"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
            
            response = requests.get(self.url, headers=headers, timeout=15)
            html_content = response.text
            
            # Padrões comuns para links de vídeo
            video_patterns = [
                r'src="([^"]+\.mp4[^"]*)"',
                r'source src="([^"]+)"',
                r'video_url=["\']([^"\' ]+\.mp4)["\']',
                r'file: ["\']([^"\' ]+\.mp4)["\']',
                r'(https?://[^\"\s<>]+\.(mp4|webm|m3u8))',
            ]
            
            for pattern in video_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                for match in matches:
                    video_url = match[0] if isinstance(match, tuple) else match
                    if self._is_valid_video_url(video_url):
                        if video_url.startswith('//'):
                            video_url = 'https:' + video_url
                        elif video_url.startswith('/'):
                            parsed = urlparse(self.url)
                            video_url = f"{parsed.scheme}://{parsed.netloc}{video_url}"
                        
                        self.status_message.emit(f"Encontrado link direto: {video_url}")
                        return self._download_direct_url(video_url)
            
            return False
        except:
            return False

    def _is_valid_video_url(self, url):
        """Verifica se é uma URL de vídeo válida"""
        video_extensions = ['.mp4', '.webm', '.m3u8', '.mkv', '.avi', '.flv', '.mov']
        return any(url.lower().endswith(ext) for ext in video_extensions)

    def _download_direct_url(self, video_url):
        """Faz download de URL direta"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': self.url,
                'Accept': '*/*',
            }
            
            # Obtém informações do arquivo
            req = urllib.request.Request(video_url, headers=headers)
            with urllib.request.urlopen(req) as response:
                file_size = int(response.headers.get('Content-Length', 0))
                
                # Gera nome do arquivo
                filename = os.path.basename(urlparse(video_url).path)
                if not filename or '.' not in filename:
                    filename = f"video_{int(time.time())}.mp4"
                
                download_path = os.path.join(self.output_path, filename)
                
                # Download com progresso
                downloaded = 0
                with open(download_path, 'wb') as f:
                    while True:
                        chunk = response.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if file_size > 0:
                            percent = (downloaded / file_size) * 100
                            self.progress_updated.emit(int(percent))
                
                self.download_finished.emit(download_path)
                return True
                
        except Exception as e:
            print(f"Erro no download direto: {e}")
            return False

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            if d.get('total_bytes'):
                percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
            elif d.get('total_bytes_estimate'):
                percent = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 100
            else:
                percent = 0
            self.progress_updated.emit(int(percent))

class VideoProcessor:
    def __init__(self):
        self.current_frame = None
        self.original_frame = None
        self.modifications = []
        
    def apply_modifications(self, frame):
        if frame is None:
            return None
            
        result = frame.copy()
        for mod in self.modifications:
            if mod['type'] == 'brightness':
                result = self.adjust_brightness(result, mod['value'])
            elif mod['type'] == 'contrast':
                result = self.adjust_contrast(result, mod['value'])
            elif mod['type'] == 'blur':
                result = self.apply_blur(result, mod['value'])
            elif mod['type'] == 'rotate':
                result = self.rotate_frame(result, mod['value'])
            elif mod['type'] == 'flip':
                result = self.flip_frame(result, mod['value'])
            elif mod['type'] == 'grayscale':
                result = self.convert_grayscale(result)
            elif mod['type'] == 'sharpen':
                result = self.sharpen_image(result)
            elif mod['type'] == 'hue':
                result = self.adjust_hue(result, mod['value'])
            elif mod['type'] == 'saturation':
                result = self.adjust_saturation(result, mod['value'])
                
        return result
        
    def adjust_brightness(self, frame, value):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        v = cv2.add(v, value)
        v = np.clip(v, 0, 255)
        final_hsv = cv2.merge((h, s, v))
        return cv2.cvtColor(final_hsv, cv2.COLOR_HSV2BGR)
        
    def adjust_contrast(self, frame, value):
        alpha = value / 100.0
        return cv2.convertScaleAbs(frame, alpha=alpha, beta=0)
        
    def apply_blur(self, frame, value):
        if value > 0:
            ksize = value if value % 2 == 1 else value + 1
            return cv2.GaussianBlur(frame, (ksize, ksize), 0)
        return frame
        
    def rotate_frame(self, frame, angle):
        (h, w) = frame.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        return cv2.warpAffine(frame, M, (w, h))
        
    def flip_frame(self, frame, flip_code):
        return cv2.flip(frame, flip_code)
        
    def convert_grayscale(self, frame):
        return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
    def sharpen_image(self, frame):
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        return cv2.filter2D(frame, -1, kernel)
        
    def adjust_hue(self, frame, value):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        h = cv2.add(h, value)
        h = np.clip(h, 0, 179)  # Hue range is 0-179 in OpenCV
        final_hsv = cv2.merge((h, s, v))
        return cv2.cvtColor(final_hsv, cv2.COLOR_HSV2BGR)
        
    def adjust_saturation(self, frame, value):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        s = cv2.add(s, value)
        s = np.clip(s, 0, 255)
        final_hsv = cv2.merge((h, s, v))
        return cv2.cvtColor(final_hsv, cv2.COLOR_HSV2BGR)
        
    def add_modification(self, mod_type, value):
        self.modifications.append({'type': mod_type, 'value': value})
        
    def clear_modifications(self):
        self.modifications = []

class VideoPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Plataforma de Gerenciamento de Vídeos Avançada")
        self.setGeometry(100, 100, 1200, 800)
        
        self.video_path = ""
        self.cap = None
        self.playing = False
        self.current_frame_pos = 0
        self.total_frames = 0
        self.fps = 0
        self.processor = VideoProcessor()
        self.downloader = None
        self.complex_downloader = None
        self.derrubador = None
        
        self.setup_ui()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        
    def setup_ui(self):
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Left panel for controls
        left_panel = QWidget()
        left_panel.setFixedWidth(400)
        left_layout = QVBoxLayout(left_panel)
        
        # URL input section
        url_group = QGroupBox("URL do Vídeo")
        url_layout = QVBoxLayout(url_group)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Cole o link do vídeo aqui...")
        url_layout.addWidget(self.url_input)
        
        url_btn_layout = QHBoxLayout()
        self.fetch_btn = QPushButton("Buscar Info")
        self.fetch_btn.clicked.connect(self.fetch_video_info)
        url_btn_layout.addWidget(self.fetch_btn)
        
        self.download_btn = QPushButton("Baixar Normal")
        self.download_btn.clicked.connect(self.download_video)
        self.download_btn.setEnabled(False)
        url_btn_layout.addWidget(self.download_btn)
        
        self.complex_download_btn = QPushButton("Download Complexo")
        self.complex_download_btn.clicked.connect(self.download_complex_video)
        self.complex_download_btn.setEnabled(True)
        url_btn_layout.addWidget(self.complex_download_btn)
        
        self.derrubar_btn = QPushButton("🚫 Derrubar Restrições")
        self.derrubar_btn.clicked.connect(self.iniciar_derrubar_restricoes)
        url_btn_layout.addWidget(self.derrubar_btn)
        
        url_layout.addLayout(url_btn_layout)
        left_layout.addWidget(url_group)
        
        # Video info section
        info_group = QGroupBox("Informações do Vídeo")
        info_layout = QVBoxLayout(info_group)
        
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        info_layout.addWidget(self.info_text)
        
        left_layout.addWidget(info_group)
        
        # Video controls section
        control_group = QGroupBox("Controles de Vídeo")
        control_layout = QVBoxLayout(control_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        control_layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Pronto")
        self.status_label.setStyleSheet("color: gray; font-style: italic;")
        control_layout.addWidget(self.status_label)
        
        # Playback controls
        playback_layout = QHBoxLayout()
        self.play_btn = QPushButton("▶ Play")
        self.play_btn.clicked.connect(self.toggle_play)
        self.play_btn.setEnabled(False)
        playback_layout.addWidget(self.play_btn)
        
        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.clicked.connect(self.stop_video)
        self.stop_btn.setEnabled(False)
        playback_layout.addWidget(self.stop_btn)
        
        self.screenshot_btn = QPushButton("📷 Capturar")
        self.screenshot_btn.clicked.connect(self.take_screenshot)
        self.screenshot_btn.setEnabled(False)
        playback_layout.addWidget(self.screenshot_btn)
        
        control_layout.addLayout(playback_layout)
        
        # Position slider
        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.sliderMoved.connect(self.set_position)
        self.position_slider.setEnabled(False)
        control_layout.addWidget(self.position_slider)
        
        left_layout.addWidget(control_group)
        
        # Video processing section
        process_group = QGroupBox("Edição de Vídeo")
        process_layout = QVBoxLayout(process_group)
        
        # Brightness control
        brightness_layout = QHBoxLayout()
        brightness_layout.addWidget(QLabel("Brilho:"))
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setRange(-100, 100)
        self.brightness_slider.setValue(0)
        self.brightness_slider.valueChanged.connect(self.adjust_brightness)
        brightness_layout.addWidget(self.brightness_slider)
        process_layout.addLayout(brightness_layout)
        
        # Contrast control
        contrast_layout = QHBoxLayout()
        contrast_layout.addWidget(QLabel("Contraste:"))
        self.contrast_slider = QSlider(Qt.Horizontal)
        self.contrast_slider.setRange(1, 300)
        self.contrast_slider.setValue(100)
        self.contrast_slider.valueChanged.connect(self.adjust_contrast)
        contrast_layout.addWidget(self.contrast_slider)
        process_layout.addLayout(contrast_layout)
        
        # Blur control
        blur_layout = QHBoxLayout()
        blur_layout.addWidget(QLabel("Blur:"))
        self.blur_slider = QSlider(Qt.Horizontal)
        self.blur_slider.setRange(0, 30)
        self.blur_slider.setValue(0)
        self.blur_slider.valueChanged.connect(self.apply_blur)
        blur_layout.addWidget(self.blur_slider)
        process_layout.addLayout(blur_layout)
        
        # Additional effects
        effects_layout = QHBoxLayout()
        self.grayscale_btn = QPushButton("⚫ Preto e Branco")
        self.grayscale_btn.clicked.connect(self.apply_grayscale)
        effects_layout.addWidget(self.grayscale_btn)
        
        self.sharpen_btn = QPushButton("🔍 Nitidez")
        self.sharpen_btn.clicked.connect(self.apply_sharpen)
        effects_layout.addWidget(self.sharpen_btn)
        process_layout.addLayout(effects_layout)
        
        # Rotation controls
        rotation_layout = QHBoxLayout()
        rotation_layout.addWidget(QLabel("Rotação:"))
        self.rotate_left_btn = QPushButton("↺ 90°")
        self.rotate_left_btn.clicked.connect(lambda: self.rotate_video(90))
        rotation_layout.addWidget(self.rotate_left_btn)
        
        self.rotate_right_btn = QPushButton("↻ 90°")
        self.rotate_right_btn.clicked.connect(lambda: self.rotate_video(-90))
        rotation_layout.addWidget(self.rotate_right_btn)
        process_layout.addLayout(rotation_layout)
        
        # Flip controls
        flip_layout = QHBoxLayout()
        flip_layout.addWidget(QLabel("Espelhar:"))
        self.flip_h_btn = QPushButton("↔ Horizontal")
        self.flip_h_btn.clicked.connect(lambda: self.flip_video(1))
        flip_layout.addWidget(self.flip_h_btn)
        
        self.flip_v_btn = QPushButton("↕ Vertical")
        self.flip_v_btn.clicked.connect(lambda: self.flip_video(0))
        flip_layout.addWidget(self.flip_v_btn)
        process_layout.addLayout(flip_layout)
        
        # Reset button
        self.reset_btn = QPushButton("🔄 Resetar")
        self.reset_btn.clicked.connect(self.reset_modifications)
        process_layout.addWidget(self.reset_btn)
        
        # Save button
        self.save_btn = QPushButton("💾 Salvar Vídeo")
        self.save_btn.clicked.connect(self.save_video)
        process_layout.addWidget(self.save_btn)
        
        left_layout.addWidget(process_group)
        left_layout.addStretch()
        
        # Right panel for video display
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setText("Vídeo não carregado")
        self.video_label.setStyleSheet("""
            border: 2px solid #ccc; 
            background-color: #f8f9fa; 
            border-radius: 8px;
            padding: 20px;
            font-style: italic;
            color: #6c757d;
        """)
        right_layout.addWidget(self.video_label)
        
        # Frame info
        self.frame_info = QLabel("Frame: 0/0 | FPS: 0")
        self.frame_info.setAlignment(Qt.AlignCenter)
        self.frame_info.setStyleSheet("color: #6c757d; font-size: 12px;")
        right_layout.addWidget(self.frame_info)
        
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)
        
    def iniciar_derrubar_restricoes(self):
        """Inicia o processo de derrubar restrições"""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Erro", "Por favor, insira uma URL válida.")
            return
            
        # Mostra diálogo de configuração
        dialog = RestricaoDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            config = dialog.get_config()
            
            self.info_text.setText("Iniciando análise de restrições...")
            self.status_label.setText("Analisando...")
            
            # Inicia o derrubador
            self.derrubador = DerrubarRestricao(
                url, 
                None if config['tipo_restricao'] == 'auto' else config['tipo_restricao'], 
                config['derrubar_ativa']
            )
            
            self.derrubador.status.connect(self.status_label.setText)
            self.derrubador.progresso.connect(self.progress_bar.setValue)
            self.derrubador.resultado.connect(self.tratar_resultado_derrubada)
            self.derrubador.video_encontrado.connect(self.tratar_video_encontrado)
            self.derrubador.start()

    def tratar_resultado_derrubada(self, mensagem, sucesso):
        """Trata o resultado da tentativa de derrubar restrições"""
        if sucesso:
            self.info_text.append(f"✅ {mensagem}")
            self.status_label.setText("Restrições derrubadas com sucesso!")
        else:
            self.info_text.append(f"❌ {mensagem}")
            self.status_label.setText("Falha ao derrubar restrições")
            
        QApplication.processEvents()

    def tratar_video_encontrado(self, video_url):
        """Trata quando uma URL de vídeo é encontrada"""
        self.info_text.append(f"🎬 URL do vídeo: {video_url}")
        
        # Pergunta se quer baixar o vídeo
        resposta = QMessageBox.question(
            self, 
            "Vídeo Encontrado", 
            f"Deseja baixar este vídeo?\n{video_url}",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if resposta == QMessageBox.Yes:
            self.url_input.setText(video_url)
            self.download_video()
        
    def fetch_video_info(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Erro", "Por favor, insira uma URL válida.")
            return
            
        try:
            self.status_label.setText("Obtendo informações...")
            self.info_text.setText("Conectando ao servidor...")
            
            # Verifica se é uma URL complexa que requer tratamento especial
            if self._is_complex_url(url):
                self.info_text.setText("URL complexa detectada. Use 'Download Complexo'.")
                self.complex_download_btn.setEnabled(True)
                return
                
            self.downloader = VideoDownloader(url)
            self.downloader.info_ready.connect(self.update_video_info)
            self.downloader.error_occurred.connect(self.show_error)
            self.downloader.status_message.connect(self.status_label.setText)
            self.downloader.start()
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao buscar informações: {str(e)}")
            
    def _is_complex_url(self, url):
        """Verifica se a URL parece ser complexa/com parâmetros especiais"""
        complex_patterns = [
            r'video\.[a-z0-9]+',  # video.ifvumvb090b
            r'\?[^=]+=[^&]+',     # Parâmetros de query
            r'#[^=]+=',           # Fragmentos com =
            r'[a-z0-9_]+=[A-Z0-9]+',  # Chave=Valor em maiúsculas
        ]
        
        return any(re.search(pattern, url, re.IGNORECASE) for pattern in complex_patterns)
            
    def update_video_info(self, info):
        try:
            # Formata as informações do vídeo
            title = info.get('title', 'N/A')
            duration = info.get('duration', 'N/A')
            uploader = info.get('uploader', 'N/A')
            view_count = info.get('view_count', 'N/A')
            upload_date = info.get('upload_date', 'N/A')
            extractor = info.get('extractor', 'N/A')
            
            # Converte a data se disponível
            if upload_date != 'N/A':
                upload_date = f"{upload_date[0:4]}-{upload_date[4:6]}-{upload_date[6:8]}"
                
            # Converte a duração se disponível
            if duration != 'N/A':
                minutes, seconds = divmod(duration, 60)
                hours, minutes = divmod(minutes, 60)
                if hours > 0:
                    duration = f"{hours}h {minutes}m {seconds}s"
                else:
                    duration = f"{minutes}m {seconds}s"
                    
            info_text = f"""
            📹 Título: {title}
            ⏱️ Duração: {duration}
            👤 Uploader: {uploader}
            👀 Visualizações: {view_count}
            📅 Data: {upload_date}
            🏷️ Fonte: {extractor}
            """
            self.info_text.setText(info_text)
            self.download_btn.setEnabled(True)
            self.status_label.setText("Informações obtidas com sucesso")
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao processar informações: {str(e)}")
            
    def download_video(self):
        try:
            url = self.url_input.text().strip()
            if not url:
                QMessageBox.warning(self, "Erro", "Por favor, insira uma URL válida.")
                return
                
            self.progress_bar.setValue(0)
            self.downloader = VideoDownloader(url)
            self.downloader.progress_updated.connect(self.progress_bar.setValue)
            self.downloader.download_finished.connect(self.video_downloaded)
            self.downloader.error_occurred.connect(self.show_error)
            self.downloader.status_message.connect(self.status_label.setText)
            self.info_text.setText("Download em andamento...")
            self.downloader.start()
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao iniciar download: {str(e)}")
            
    def download_complex_video(self):
        """Método especial para URLs complexas"""
        try:
            url = self.url_input.text().strip()
            if not url:
                QMessageBox.warning(self, "Erro", "Por favor, insira uma URL válida.")
                return
                
            self.progress_bar.setValue(0)
            self.status_label.setText("Processando URL complexa...")
            self.info_text.setText("Iniciando download complexo...\nIsso pode demorar alguns minutos.")
            
            self.complex_downloader = ComplexVideoDownloader(url)
            self.complex_downloader.progress_updated.connect(self.progress_bar.setValue)
            self.complex_downloader.download_finished.connect(self.video_downloaded)
            self.complex_downloader.error_occurred.connect(self.show_error)
            self.complex_downloader.status_message.connect(self.status_label.setText)
            self.complex_downloader.info_ready.connect(self.update_video_info)
            self.complex_downloader.start()
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro no download complexo: {str(e)}")
            
    def video_downloaded(self, filepath):
        try:
            self.video_path = filepath
            filename = os.path.basename(filepath)
            self.info_text.setText(f"✅ Download concluído:\n{filename}")
            self.status_label.setText("Vídeo carregado com sucesso")
            
            # Habilita controles de vídeo
            self.play_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)
            self.screenshot_btn.setEnabled(True)
            self.position_slider.setEnabled(True)
            
            # Carrega o vídeo
            self.load_video(filepath)
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar vídeo: {str(e)}")
            
    def load_video(self, filepath):
        try:
            self.cap = cv2.VideoCapture(filepath)
            if not self.cap.isOpened():
                raise Exception("Não foi possível abrir o vídeo")
                
            self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.fps = self.cap.get(cv2.CAP_PROP_FPS)
            
            self.position_slider.setRange(0, self.total_frames)
            self.update_frame_info()
            
            # Mostra o primeiro frame
            ret, frame = self.cap.read()
            if ret:
                self.processor.original_frame = frame
                self.processor.current_frame = frame
                self.display_frame(frame)
                
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar vídeo: {str(e)}")
            
    def update_frame(self):
        if self.playing and self.cap is not None:
            ret, frame = self.cap.read()
            if ret:
                self.current_frame_pos += 1
                processed_frame = self.processor.apply_modifications(frame)
                self.display_frame(processed_frame)
                self.position_slider.setValue(self.current_frame_pos)
                self.update_frame_info()
            else:
                self.stop_video()
                
    def display_frame(self, frame):
        if frame is not None:
            # Converte BGR para RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Redimensiona se necessário
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            
            # Ajusta ao tamanho do label
            pixmap = QPixmap.fromImage(qt_image)
            scaled_pixmap = pixmap.scaled(self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.video_label.setPixmap(scaled_pixmap)
            
    def update_frame_info(self):
        self.frame_info.setText(f"Frame: {self.current_frame_pos}/{self.total_frames} | FPS: {self.fps:.1f}")
        
    def toggle_play(self):
        if not self.playing:
            self.playing = True
            self.play_btn.setText("⏸ Pause")
            self.timer.start(1000 / self.fps)
        else:
            self.playing = False
            self.play_btn.setText("▶ Play")
            self.timer.stop()
            
    def stop_video(self):
        self.playing = False
        self.play_btn.setText("▶ Play")
        self.timer.stop()
        
        if self.cap is not None:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self.current_frame_pos = 0
            self.position_slider.setValue(0)
            
            ret, frame = self.cap.read()
            if ret:
                processed_frame = self.processor.apply_modifications(frame)
                self.display_frame(processed_frame)
                self.update_frame_info()
                
    def set_position(self, position):
        if self.cap is not None:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, position)
            self.current_frame_pos = position
            ret, frame = self.cap.read()
            if ret:
                processed_frame = self.processor.apply_modifications(frame)
                self.display_frame(processed_frame)
                self.update_frame_info()
                
    def take_screenshot(self):
        if self.processor.current_frame is not None:
            filepath, _ = QFileDialog.getSaveFileName(
                self, "Salvar Captura", "", "Imagens (*.png *.jpg *.bmp)"
            )
            if filepath:
                cv2.imwrite(filepath, self.processor.current_frame)
                self.status_label.setText(f"Captura salva: {filepath}")
                
    def adjust_brightness(self, value):
        self.processor.add_modification('brightness', value)
        self.apply_modifications()
        
    def adjust_contrast(self, value):
        self.processor.add_modification('contrast', value)
        self.apply_modifications()
        
    def apply_blur(self, value):
        self.processor.add_modification('blur', value)
        self.apply_modifications()
        
    def apply_grayscale(self):
        self.processor.add_modification('grayscale', 0)
        self.apply_modifications()
        
    def apply_sharpen(self):
        self.processor.add_modification('sharpen', 0)
        self.apply_modifications()
        
    def rotate_video(self, angle):
        self.processor.add_modification('rotate', angle)
        self.apply_modifications()
        
    def flip_video(self, flip_code):
        self.processor.add_modification('flip', flip_code)
        self.apply_modifications()
        
    def apply_modifications(self):
        if self.processor.original_frame is not None:
            processed_frame = self.processor.apply_modifications(self.processor.original_frame.copy())
            self.processor.current_frame = processed_frame
            self.display_frame(processed_frame)
            
    def reset_modifications(self):
        self.processor.clear_modifications()
        self.brightness_slider.setValue(0)
        self.contrast_slider.setValue(100)
        self.blur_slider.setValue(0)
        
        if self.processor.original_frame is not None:
            self.processor.current_frame = self.processor.original_frame.copy()
            self.display_frame(self.processor.original_frame)
            
    def save_video(self):
        if self.video_path:
            options = QFileDialog.Options()
            filepath, _ = QFileDialog.getSaveFileName(
                self, "Salvar Vídeo", "", "Vídeos (*.mp4 *.avi *.mov)", options=options
            )
            if filepath:
                # Aqui você implementaria a lógica para salvar o vídeo com as modificações
                self.status_label.setText("Funcionalidade de salvar vídeo em desenvolvimento")
                
    def show_error(self, error_msg):
        QMessageBox.critical(self, "Erro", error_msg)
        self.status_label.setText("Erro ocorrido")
        
    def closeEvent(self, event):
        if self.cap is not None:
            self.cap.release()
        if self.downloader and self.downloader.isRunning():
            self.downloader.terminate()
        if self.complex_downloader and self.complex_downloader.isRunning():
            self.complex_downloader.terminate()
        if self.derrubador and self.derrubador.isRunning():
            self.derrubador.terminate()
        event.accept()

def main():
    app = QApplication(sys.argv)
    player = VideoPlayer()
    player.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()