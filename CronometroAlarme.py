import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import pygame
import time
import threading
import os
import json
from datetime import datetime
from pygame import mixer

class CronometroAlarme:
    def __init__(self, root):
        self.root = root
        self.root.title("Relógio e Cronômetro 3.0")
        
        # Configuração de posicionamento
        self.configurar_tamanho_posicao()
        
        # Variáveis de controle de execução
        self.should_stop = False
        self.running_threads = []
        
        # Inicialização do mixer
        mixer.init()
        
        # Variáveis de controle
        self.tempo_restante = 0
        self.tempo_total = 0
        self.cronometro_rodando = False
        self.arquivo_alarme = self.carregar_alarme_padrao()
        self.alarmes_salvos = []
        self.sequencia_alarmes = []
        self.indice_alarme_atual = 0
        
        self.carregar_alarmes()
        self.configurar_interface()
        self.atualizar_relogio_titulo()
        
        # Garante que o programa feche corretamente
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def configurar_tamanho_posicao(self):
        """Configura o tamanho e posição da janela"""
        largura_janela = 450
        altura_janela = 690
        
        # Calcula a posição para ficar no topo com 20% de margem no rodapé
        altura_tela = self.root.winfo_screenheight()
        pos_x = (self.root.winfo_screenwidth() - largura_janela) // 2
        pos_y = 0  # Topo da tela
        
        self.root.geometry(f"{largura_janela}x{altura_janela}+{pos_x}+{pos_y}")
        self.root.resizable(False, False)

    def on_close(self):
        """Método chamado quando a janela é fechada"""
        self.should_stop = True
        self.cronometro_rodando = False
        
        # Para todas as threads em execução
        for thread in self.running_threads:
            if thread.is_alive():
                thread.join(timeout=0.5)
        
        # Para qualquer som que esteja tocando
        mixer.music.stop()
        
        # Fecha a janela
        self.root.destroy()

    def atualizar_relogio_titulo(self):
        """Atualiza o relógio digital na barra de título"""
        if self.should_stop or not self.root.winfo_exists():
            return
        
        agora = datetime.now()
        data_formatada = agora.strftime("%d/%m/%Y")
        hora_formatada = agora.strftime("%H:%M:%S")
        self.root.title(f"Relógio e Cronômetro 3.0 - {data_formatada} - {hora_formatada}")
        self.root.after(1000, self.atualizar_relogio_titulo)

    def carregar_alarme_padrao(self):
        """Tenta carregar um arquivo alarme.mp3 na mesma pasta do programa"""
        try:
            caminho_padrao = os.path.join(os.path.dirname(__file__), "alarme.mp3")
            if os.path.exists(caminho_padrao):
                return caminho_padrao
            caminho_windows = "C:/Windows/Media/Alarm01.wav"
            if os.path.exists(caminho_windows):
                return caminho_windows
            return None
        except Exception as e:
            print(f"Erro ao carregar alarme padrão: {e}")
            return None

    def configurar_interface(self):
        """Configura todos os elementos da interface"""
        # Frame principal
        frame_principal = tk.Frame(self.root)
        frame_principal.pack(pady=10)
        
        # Display do cronômetro
        self.label_tempo = tk.Label(frame_principal, text="00:00:00", font=("Arial", 40))
        self.label_tempo.pack(pady=10)
        
        # Barra de progresso
        self.progressbar = ttk.Progressbar(
            self.root, 
            orient='horizontal', 
            mode='determinate', 
            length=400
        )
        self.progressbar.pack(pady=5)
        
        # Entrada de tempo
        self.entry_tempo = tk.Entry(self.root, font=("Arial", 12), width=25)
        self.entry_tempo.insert(0, "MM:SS  HH:MM:SS")
        self.entry_tempo.bind("<FocusIn>", self.limpar_placeholder)
        self.entry_tempo.pack(pady=5)
        
        # Frame para botões principais
        frame_botoes = tk.Frame(self.root)
        frame_botoes.pack(pady=5)
        
        # Coluna 1 - Botões de controle
        frame_col1 = tk.Frame(frame_botoes)
        frame_col1.pack(side=tk.LEFT, padx=5)
        
        btn_iniciar = tk.Button(
            frame_col1,
            text="Iniciar",
            command=self.iniciar_cronometro,
            bg="#27ae60",
            fg="white",
            font=("Arial", 10, "bold"),
            width=12,
            relief=tk.RAISED,
            bd=2
        )
        btn_iniciar.pack(pady=2)
        
        self.btn_parar = tk.Button(
            frame_col1,
            text="Parar",
            command=self.parar_cronometro,
            bg="#e74c3c",
            fg="white",
            font=("Arial", 10, "bold"),
            width=12,
            relief=tk.RAISED,
            bd=2,
            state=tk.DISABLED
        )
        self.btn_parar.pack(pady=2)
        
        # Coluna 2 - Botões de som
        frame_col2 = tk.Frame(frame_botoes)
        frame_col2.pack(side=tk.LEFT, padx=5)
        
        btn_selecionar = tk.Button(
            frame_col2,
            text="Selecionar Som",
            command=self.selecionar_alarme,
            bg="#f1c40f",
            fg="black",
            font=("Arial", 10, "bold"),
            width=12,
            relief=tk.RAISED,
            bd=2
        )
        btn_selecionar.pack(pady=2)
        
        btn_testar = tk.Button(
            frame_col2,
            text="Testar Alarme",
            command=self.tocar_alarme_teste,
            bg="#f1c40f",
            fg="black",
            font=("Arial", 10, "bold"),
            width=12,
            relief=tk.RAISED,
            bd=2
        )
        btn_testar.pack(pady=2)
        
        # Botão Salvar Alarme
        self.btn_salvar_alarme = tk.Button(
            self.root,
            text="Salvar Alarme",
            command=self.salvar_alarme,
            bg="#9b59b6",
            fg="white",
            font=("Arial", 10, "bold"),
            width=25,
            relief=tk.RAISED,
            bd=2
        )
        self.btn_salvar_alarme.pack(pady=5)
        
        # Lista de alarmes salvos
        self.label_lista = tk.Label(self.root, text="Alarmes Salvos:", font=("Arial", 10))
        self.label_lista.pack(pady=5)
        
        self.lista_alarmes = tk.Listbox(self.root, height=6, width=50)
        self.lista_alarmes.pack(pady=5)
        self.atualizar_lista_alarmes()
        
        # Lista de sequência
        self.label_sequencia = tk.Label(self.root, text="Sequência Atual:", font=("Arial", 10))
        self.label_sequencia.pack(pady=5)
        
        self.lista_sequencia = tk.Listbox(self.root, height=6, width=50)
        self.lista_sequencia.pack(pady=5)
        
        # Frame para botões de sequência
        frame_sequencia = tk.Frame(self.root)
        frame_sequencia.pack(pady=5)
        
        btn_adicionar = tk.Button(
            frame_sequencia,
            text="Adicionar à Sequência",
            command=self.adicionar_a_sequencia,
            bg="#3498db",
            fg="white",
            font=("Arial", 10, "bold"),
            width=18,
            relief=tk.RAISED,
            bd=2
        )
        btn_adicionar.pack(side=tk.LEFT, padx=5)
        
        self.btn_criar_sequencia = tk.Button(
            frame_sequencia,
            text="Criar Sequência",
            command=self.criar_sequencia,
            bg="#3498db",
            fg="white",
            font=("Arial", 10, "bold"),
            width=15,
            relief=tk.RAISED,
            bd=2
        )
        self.btn_criar_sequencia.pack(side=tk.LEFT, padx=5)
        
        # Frame para botões de gerenciamento
        frame_gerenciamento = tk.Frame(self.root)
        frame_gerenciamento.pack(pady=5)
        
        btn_usar = tk.Button(
            frame_gerenciamento,
            text="Usar Alarme",
            command=self.usar_alarme_selecionado,
            bg="#27ae60",
            fg="white",
            font=("Arial", 10, "bold"),
            width=15,
            relief=tk.RAISED,
            bd=2
        )
        btn_usar.pack(side=tk.LEFT, padx=5)
        
        btn_remover = tk.Button(
            frame_gerenciamento,
            text="Remover",
            command=self.remover_alarme_selecionado,
            bg="#e74c3c",
            fg="white",
            font=("Arial", 10, "bold"),
            width=15,
            relief=tk.RAISED,
            bd=2
        )
        btn_remover.pack(side=tk.LEFT, padx=5)

        # Frame para a marca d'água no rodapé
        frame_rodape = tk.Frame(self.root)
        frame_rodape.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        
        lbl_marca = tk.Label(
            frame_rodape,
            text="© Todos os direitos reservados YsneshY-YXK",
            font=("Arial", 8),
            fg="gray"
        )
        lbl_marca.pack()

    def limpar_placeholder(self, event):
        if self.entry_tempo.get() == "MM:SS  HH:MM:SS":
            self.entry_tempo.delete(0, tk.END)

    def carregar_alarmes(self):
        try:
            if os.path.exists("alarmes.json"):
                with open("alarmes.json", "r") as f:
                    self.alarmes_salvos = json.load(f)
        except Exception as e:
            print(f"Erro ao carregar alarmes: {e}")

    def salvar_alarmes(self):
        try:
            with open("alarmes.json", "w") as f:
                json.dump(self.alarmes_salvos, f)
        except Exception as e:
            print(f"Erro ao salvar alarmes: {e}")

    def atualizar_lista_alarmes(self):
        self.lista_alarmes.delete(0, tk.END)
        for alarme in self.alarmes_salvos:
            self.lista_alarmes.insert(tk.END, f"{alarme['nome']} - {alarme['tempo']}")

    def atualizar_lista_sequencia(self):
        self.lista_sequencia.delete(0, tk.END)
        for i, alarme in enumerate(self.sequencia_alarmes, 1):
            self.lista_sequencia.insert(tk.END, f"{i}. {alarme['nome']} - {alarme['tempo']}")

    def converter_para_segundos(self, tempo_str):
        partes = tempo_str.split(':')
        try:
            if len(partes) == 1:
                return int(partes[0])
            elif len(partes) == 2:
                return int(partes[0]) * 60 + int(partes[1])
            elif len(partes) == 3:
                return int(partes[0]) * 3600 + int(partes[1]) * 60 + int(partes[2])
        except ValueError:
            return None

    def selecionar_alarme(self):
        arquivo = filedialog.askopenfilename(
            title="Selecione um arquivo de som",
            filetypes=[("Arquivos de Áudio", "*.mp3 *.wav")]
        )
        if arquivo:
            self.arquivo_alarme = arquivo
            messagebox.showinfo("Sucesso", f"Alarme definido:\n{os.path.basename(arquivo)}")

    def salvar_alarme(self):
        tempo_str = self.entry_tempo.get()
        segundos = self.converter_para_segundos(tempo_str)
        
        if segundos is None or segundos <= 0:
            messagebox.showerror("Erro", "Formato de tempo inválido!")
            return
        
        if not self.arquivo_alarme:
            messagebox.showwarning("Aviso", "Nenhum arquivo de som selecionado!")
            return
        
        nome = simpledialog.askstring("Nome do Alarme", "Digite um nome para este alarme:")
        if nome:
            novo_alarme = {
                "nome": nome,
                "tempo": tempo_str,
                "arquivo": self.arquivo_alarme,
                "segundos": segundos
            }
            self.alarmes_salvos.append(novo_alarme)
            self.salvar_alarmes()
            self.atualizar_lista_alarmes()
            messagebox.showinfo("Sucesso", "Alarme salvo com sucesso!")

    def usar_alarme_selecionado(self):
        selecao = self.lista_alarmes.curselection()
        if not selecao:
            messagebox.showwarning("Aviso", "Selecione um alarme na lista!")
            return
        
        alarme = self.alarmes_salvos[selecao[0]]
        self.entry_tempo.delete(0, tk.END)
        self.entry_tempo.insert(0, alarme["tempo"])
        self.arquivo_alarme = alarme["arquivo"]
        messagebox.showinfo("Alarme Carregado", f"Pronto para usar: {alarme['nome']}")

    def adicionar_a_sequencia(self):
        selecao = self.lista_alarmes.curselection()
        if not selecao:
            messagebox.showwarning("Aviso", "Selecione um alarme na lista!")
            return
        
        alarme = self.alarmes_salvos[selecao[0]]
        self.sequencia_alarmes.append(alarme)
        self.atualizar_lista_sequencia()
        messagebox.showinfo("Sucesso", f"Alarme '{alarme['nome']}' adicionado à sequência!")

    def criar_sequencia(self):
        if not self.sequencia_alarmes:
            messagebox.showwarning("Aviso", "Adicione alarmes à sequência primeiro!")
            return
        
        self.indice_alarme_atual = 0
        self.iniciar_proximo_alarme()

    def iniciar_proximo_alarme(self):
        if self.should_stop:
            return
            
        if self.indice_alarme_atual >= len(self.sequencia_alarmes):
            messagebox.showinfo("Sequência Completa", "Todos os alarmes da sequência foram concluídos!")
            return
        
        alarme = self.sequencia_alarmes[self.indice_alarme_atual]
        self.entry_tempo.delete(0, tk.END)
        self.entry_tempo.insert(0, alarme["tempo"])
        self.arquivo_alarme = alarme["arquivo"]
        self.tempo_restante = alarme["segundos"]
        self.tempo_total = alarme["segundos"]
        
        # Configura a barra de progresso
        self.progressbar['maximum'] = self.tempo_total
        self.progressbar['value'] = self.tempo_restante
        
        self.label_tempo.config(text=alarme["tempo"])
        messagebox.showinfo("Próximo Alarme", f"Iniciando: {alarme['nome']} - {alarme['tempo']}")
        
        self.cronometro_rodando = True
        self.btn_parar.config(state=tk.NORMAL)
        
        thread = threading.Thread(target=self.atualizar_cronometro_sequencial, daemon=True)
        self.running_threads.append(thread)
        thread.start()

    def remover_alarme_selecionado(self):
        selecao = self.lista_alarmes.curselection()
        if not selecao:
            messagebox.showwarning("Aviso", "Selecione um alarme para remover!")
            return
        
        self.alarmes_salvos.pop(selecao[0])
        self.salvar_alarmes()
        self.atualizar_lista_alarmes()

    def iniciar_cronometro(self):
        tempo_str = self.entry_tempo.get()
        segundos = self.converter_para_segundos(tempo_str)
        
        if segundos is None or segundos <= 0:
            messagebox.showerror("Erro", "Formato de tempo inválido!")
            return
        
        self.tempo_restante = segundos
        self.tempo_total = segundos
        self.cronometro_rodando = True
        self.btn_parar.config(state=tk.NORMAL)
        
        # Configura a barra de progresso
        self.progressbar['maximum'] = segundos
        self.progressbar['value'] = segundos
        
        thread = threading.Thread(target=self.atualizar_cronometro, daemon=True)
        self.running_threads.append(thread)
        thread.start()

    def parar_cronometro(self):
        self.cronometro_rodando = False
        self.btn_parar.config(state=tk.DISABLED)
        self.label_tempo.config(text="00:00:00")
        self.progressbar['value'] = 0

    def atualizar_cronometro(self):
        while not self.should_stop and self.cronometro_rodando and self.tempo_restante > 0:
            horas = self.tempo_restante // 3600
            minutos = (self.tempo_restante % 3600) // 60
            segundos = self.tempo_restante % 60
            tempo_formatado = f"{horas:02d}:{minutos:02d}:{segundos:02d}"
            
            # Atualiza a interface na thread principal
            if not self.should_stop and self.root.winfo_exists():
                self.root.after(0, self.atualizar_interface_tempo, tempo_formatado, self.tempo_restante)
            
            time.sleep(1)
            self.tempo_restante -= 1
        
        if not self.should_stop and self.tempo_restante <= 0 and self.cronometro_rodando:
            self.cronometro_rodando = False
            if self.root.winfo_exists():
                self.root.after(0, self.tocar_alarme)
                self.root.after(0, lambda: self.btn_parar.config(state=tk.DISABLED))

    def atualizar_cronometro_sequencial(self):
        while not self.should_stop and self.cronometro_rodando and self.tempo_restante > 0:
            horas = self.tempo_restante // 3600
            minutos = (self.tempo_restante % 3600) // 60
            segundos = self.tempo_restante % 60
            tempo_formatado = f"{horas:02d}:{minutos:02d}:{segundos:02d}"
            
            # Atualiza a interface na thread principal
            if not self.should_stop and self.root.winfo_exists():
                self.root.after(0, self.atualizar_interface_tempo, tempo_formatado, self.tempo_restante)
            
            time.sleep(1)
            self.tempo_restante -= 1
        
        if not self.should_stop and self.tempo_restante <= 0 and self.cronometro_rodando:
            self.cronometro_rodando = False
            if self.root.winfo_exists():
                self.root.after(0, self.tocar_alarme_sequencial)

    def atualizar_interface_tempo(self, tempo_formatado, tempo_restante):
        """Atualiza o label do tempo e a barra de progresso"""
        if self.should_stop or not self.root.winfo_exists():
            return
            
        self.label_tempo.config(text=tempo_formatado)
        self.progressbar['value'] = tempo_restante
        
        # Atualiza a cor conforme o progresso
        progresso = (tempo_restante / self.tempo_total) * 100
        if progresso < 20:
            self.progressbar.configure(style="red.Horizontal.TProgressbar")
        elif progresso < 50:
            self.progressbar.configure(style="yellow.Horizontal.TProgressbar")
        else:
            self.progressbar.configure(style="green.Horizontal.TProgressbar")

    def tocar_alarme(self):
        try:
            if self.should_stop or not self.root.winfo_exists():
                return
                
            if self.arquivo_alarme:
                mixer.music.load(self.arquivo_alarme)
            else:
                mixer.music.load("C:/Windows/Media/Alarm01.wav")
            
            mixer.music.play(loops=-1)
            
            if not self.should_stop and self.root.winfo_exists():
                resposta = messagebox.askokcancel(
                    "Alarme", 
                    "⏰ Tempo acabado!\n\nClique OK para parar o alarme.",
                    icon='warning'
                )
            
            mixer.music.stop()
            
        except pygame.error as e:
            if not self.should_stop and self.root.winfo_exists():
                messagebox.showerror("Erro", f"Problema com o arquivo de som:\n{e}")
        except Exception as e:
            if not self.should_stop and self.root.winfo_exists():
                messagebox.showerror("Erro", f"Falha inesperada: {e}")
        finally:
            mixer.music.stop()

    def tocar_alarme_sequencial(self):
        try:
            if self.should_stop or not self.root.winfo_exists():
                return
                
            if self.arquivo_alarme:
                mixer.music.load(self.arquivo_alarme)
            else:
                mixer.music.load("C:/Windows/Media/Alarm01.wav")
            
            mixer.music.play(loops=-1)
            
            if not self.should_stop and self.root.winfo_exists():
                alarme_atual = self.sequencia_alarmes[self.indice_alarme_atual]
                resposta = messagebox.askokcancel(
                    "Alarme Concluído", 
                    f"⏰ {alarme_atual['nome']} concluído!\n\nClique OK para continuar para o próximo alarme.",
                    icon='warning'
                )
            
            mixer.music.stop()
            
            if not self.should_stop:
                self.indice_alarme_atual += 1
                if self.root.winfo_exists():
                    self.root.after(0, self.iniciar_proximo_alarme)
            
        except pygame.error as e:
            if not self.should_stop and self.root.winfo_exists():
                messagebox.showerror("Erro", f"Problema com o arquivo de som:\n{e}")
                self.parar_cronometro()
        except Exception as e:
            if not self.should_stop and self.root.winfo_exists():
                messagebox.showerror("Erro", f"Falha inesperada: {e}")
                self.parar_cronometro()
        finally:
            mixer.music.stop()

    def tocar_alarme_teste(self):
        if self.should_stop:
            return
            
        thread = threading.Thread(target=self.tocar_alarme, daemon=True)
        self.running_threads.append(thread)
        thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    
    # Configura estilos para a barra de progresso
    style = ttk.Style()
    style.theme_use('clam')
    style.configure("green.Horizontal.TProgressbar", foreground='green', background='green')
    style.configure("yellow.Horizontal.TProgressbar", foreground='yellow', background='yellow')
    style.configure("red.Horizontal.TProgressbar", foreground='red', background='red')
    
    app = CronometroAlarme(root)
    root.mainloop()
