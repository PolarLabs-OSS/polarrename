"""PolarRename 1.0 — offline batch file renamer, PolarLabs-OSS."""
from pathlib import Path
from dataclasses import dataclass
from collections import Counter
import os
import uuid
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

BG="#091623"; PANEL="#122537"; FG="#EAF6FA"; ACC="#27D6D0"; MUTED="#9BB5C2"

@dataclass
class Rules:
    prefix:str=""
    suffix:str=""
    search:str=""
    replace:str=""
    numbered:bool=False
    start:int=1
    digits:int=3
    extension:bool=False

def plan(paths, rules):
    pairs=[]
    for idx, path in enumerate(paths):
        source=Path(path)
        stem=source.stem
        ext=source.suffix
        if rules.extension:
            base=source.name
            ext=""
        else:
            base=stem
        if rules.search:
            base=base.replace(rules.search,rules.replace)
        name=rules.prefix+base+rules.suffix
        if rules.numbered:
            name+=f"_{rules.start+idx:0{rules.digits}d}"
        target=source.with_name(name+ext)
        pairs.append((source,target))
    validate(pairs)
    return pairs

def validate(pairs):
    sources={os.path.normcase(str(a.resolve())) for a,b in pairs}
    destinations=[os.path.normcase(str(b.resolve())) for a,b in pairs]
    if len(destinations)!=len(set(destinations)):
        raise ValueError("Nomi di destinazione duplicati.")
    for source,target in pairs:
        if not target.name or target.name in (".",".."):
            raise ValueError("Nome file vuoto.")
        if os.name=="nt" and (any(c in target.name for c in '<>:"/\\|?*') or target.stem.rstrip(" .")!=target.stem):
            raise ValueError(f"Nome non valido: {target.name}")
        if not source.is_file():
            raise ValueError(f"File non trovato: {source}")
        if target.exists() and os.path.normcase(str(target.resolve())) not in sources:
            raise ValueError(f"File già esistente: {target.name}")
    return True

def apply(pairs):
    moves=[(a,b) for a,b in pairs if a!=b]
    validate(pairs)
    if not moves:return []
    stages=[]
    completed=[]
    try:
        for source,target in moves:
            temp=source.with_name(".__polar_"+uuid.uuid4().hex+".tmp")
            os.replace(source,temp)
            stages.append((source,temp,target))
        for source,temp,target in stages:
            os.replace(temp,target)
            completed.append((source,target))
        return completed
    except Exception:
        for source,target in reversed(completed):
            if target.exists():os.replace(target,source)
        for source,temp,target in reversed(stages):
            if temp.exists():os.replace(temp,source)
        raise

class App:
    def __init__(self,root):
        self.root=root
        self.root.title("PolarRename | PolarLabs-OSS")
        self.root.geometry("1060x730")
        self.root.configure(bg=BG)
        self.paths=[]
        self.undo_pairs=[]
        frame=tk.Frame(root,bg=BG,padx=26,pady=20);frame.pack(fill="both",expand=True)
        tk.Label(frame,text="POLAR / RENAME",fg=ACC,bg=BG,font=("Segoe UI",26,"bold")).pack(anchor="w")
        tk.Label(frame,text="Rinomina in massa  •  Anteprima prima di applicare  •  Nessun cloud",fg=MUTED,bg=BG).pack(anchor="w",pady=(0,15))
        bar=tk.Frame(frame,bg=BG);bar.pack(fill="x",pady=5)
        for label,func in [("+ Aggiungi file",self.add),("Aggiungi cartella",self.folder),("Svuota",self.clear)]:
            self.button(bar,label,func).pack(side="left",padx=(0,8))
        opts=tk.Frame(frame,bg=PANEL,padx=15,pady=14);opts.pack(fill="x",pady=(10,12))
        self.fields={}
        for i,(label,field) in enumerate([("Prefisso","prefix"),("Suffisso","suffix"),("Trova","search"),("Sostituisci con","replace")]):
            box=tk.Frame(opts,bg=PANEL);box.grid(row=i//2,column=i%2,sticky="ew",padx=8,pady=6)
            tk.Label(box,text=label,bg=PANEL,fg=FG).pack(side="left",padx=(0,12))
            var=tk.StringVar();var.trace_add("write",lambda *_:self.preview())
            self.fields[field]=var
            tk.Entry(box,textvariable=var,bg=BG,fg=FG,insertbackground=FG,relief="flat").pack(side="left",fill="x",expand=True,ipady=6)
        opts.grid_columnconfigure(0,weight=1);opts.grid_columnconfigure(1,weight=1)
        switches=tk.Frame(opts,bg=PANEL);switches.grid(row=2,column=0,columnspan=2,sticky="w",padx=8,pady=8)
        self.numbered=tk.BooleanVar(value=False);self.ext=tk.BooleanVar(value=False)
        tk.Checkbutton(switches,text="Numerazione progressiva",variable=self.numbered,command=self.preview,fg=FG,bg=PANEL,selectcolor=BG,activebackground=PANEL,activeforeground=FG).pack(side="left")
        tk.Checkbutton(switches,text="Modifica anche estensione",variable=self.ext,command=self.preview,fg=FG,bg=PANEL,selectcolor=BG,activebackground=PANEL,activeforeground=FG).pack(side="left",padx=(30,10))
        self.start=tk.StringVar(value="1");self.digits=tk.StringVar(value="3")
        for label,var in [("Da",self.start),("Cifre",self.digits)]:
            tk.Label(switches,text=label,bg=PANEL,fg=FG).pack(side="left",padx=(8,4))
            tk.Spinbox(switches,from_=1,to=999999,width=5,textvariable=var,command=self.preview,bg=BG,fg=FG).pack(side="left")
            var.trace_add("write",lambda *_:self.preview())
        style=ttk.Style();style.theme_use("clam")
        style.configure("Treeview",background=PANEL,fieldbackground=PANEL,foreground=FG,rowheight=28)
        style.configure("Treeview.Heading",background="#1B3850",foreground=FG)
        self.tree=ttk.Treeview(frame,columns=("original","new","state"),show="headings")
        for name,title,width in [("original","Originale",360),("new","Nuovo nome",360),("state","Stato",130)]:
            self.tree.heading(name,text=title);self.tree.column(name,width=width)
        self.tree.pack(fill="both",expand=True)
        bottom=tk.Frame(frame,bg=BG);bottom.pack(fill="x",pady=(15,5))
        self.button(bottom,"Applica rinomina",self.rename,primary=True).pack(side="left",padx=(0,10))
        self.button(bottom,"Annulla ultima operazione",self.undo).pack(side="left")
        self.status=tk.StringVar(value="Pronto")
        tk.Label(frame,textvariable=self.status,fg=MUTED,bg=BG).pack(anchor="w",pady=8)
        tk.Label(frame,text="PolarLabs-OSS  •  Elaborazione locale  •  Consiglio: fare un backup dei file importanti",fg=MUTED,bg=BG,font=("Segoe UI",8)).pack(anchor="w")
    def button(self,parent,label,func,primary=False):
        return tk.Button(parent,text=label,command=func,bg=ACC if primary else PANEL,fg=BG if primary else FG,padx=13,pady=8,relief="flat")
    def rules(self):
        return Rules(**{k:v.get() for k,v in self.fields.items()},numbered=self.numbered.get(),extension=self.ext.get(),start=int(self.start.get()),digits=int(self.digits.get()))
    def add_paths(self,paths):
        for p in paths:
            p=Path(p)
            if p.is_file() and p not in self.paths:self.paths.append(p)
        self.preview()
    def add(self):self.add_paths(filedialog.askopenfilenames())
    def folder(self):
        p=filedialog.askdirectory()
        if p:self.add_paths(x for x in Path(p).iterdir() if x.is_file())
    def clear(self):
        self.paths=[];self.preview()
    def preview(self):
        for row in self.tree.get_children():self.tree.delete(row)
        try:
            pairs=plan(self.paths,self.rules())
            for src,dst in pairs:self.tree.insert("","end",values=(src.name,dst.name,"Invariato" if src==dst else "Pronto"))
            self.status.set(f"{len(pairs)} file  •  {sum(a!=b for a,b in pairs)} da rinominare")
            self.valid=True
        except Exception as e:
            self.status.set("ATTENZIONE: "+str(e))
            self.valid=False
    def rename(self):
        if not self.paths or not self.valid:return
        try:pairs=plan(self.paths,self.rules())
        except Exception as e:return messagebox.showerror("PolarRename",str(e))
        count=sum(a!=b for a,b in pairs)
        if not count:return
        if not messagebox.askyesno("Conferma",f"Rinominare {count} file?"):return
        try:
            moved=apply(pairs)
            self.undo_pairs=moved
            self.paths=[b for a,b in pairs]
            self.preview()
            self.status.set(f"Completato: {len(moved)} file rinominati")
        except Exception as e:messagebox.showerror("Errore",str(e))
    def undo(self):
        if not self.undo_pairs:return messagebox.showinfo("PolarRename","Nessuna operazione da annullare")
        try:
            reverse=[(b,a) for a,b in self.undo_pairs]
            apply(reverse)
            remap=dict(reverse)
            self.paths=[remap.get(p,p) for p in self.paths]
            self.undo_pairs=[]
            self.preview()
            self.status.set("Ultima rinomina annullata")
        except Exception as e:messagebox.showerror("Errore annullamento",str(e))

from ui_theme import apply_theme

if __name__=="__main__":
    root=tk.Tk();App(root);apply_theme(root);root.mainloop()
