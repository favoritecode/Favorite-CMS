"use client";

import { type FormEvent, type ReactNode, useEffect, useRef, useState } from "react";
import { EditorContent, useEditor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import TextAlign from "@tiptap/extension-text-align";
import Image from "@tiptap/extension-image";
import Placeholder from "@tiptap/extension-placeholder";
import {
  AlignCenter, AlignJustify, AlignLeft, AlignRight, Bold, Braces, Code, Heading1, Heading2,
  Heading3, ImagePlus, Italic, Link as LinkIcon, List, ListOrdered, Minus, Pilcrow,
  Quote, Redo2, RemoveFormatting, Strikethrough, Underline, Undo2, X,
} from "lucide-react";
import { fieldClass, primaryButton, secondaryButton } from "./admin-ui";
import { validArticleUrl } from "@/lib/content-editor";

type Dialog = "link" | "image" | null;

export function ArticleEditor({ value, onChange, disabled = false }: {
  value: string; onChange: (value: string) => void; disabled?: boolean;
}) {
  const [mode, setMode] = useState<"rich" | "source">("rich");
  const [dialog, setDialog] = useState<Dialog>(null);
  const [, setRevision] = useState(0);
  const onChangeRef = useRef(onChange);
  useEffect(() => { onChangeRef.current = onChange; }, [onChange]);

  const editor = useEditor({
    immediatelyRender: false,
    editable: !disabled,
    editorProps: { attributes: { "aria-label": "Body", role: "textbox" } },
    extensions: [
      StarterKit.configure({
        heading: { levels: [1, 2, 3] },
        link: { openOnClick: false, HTMLAttributes: { rel: "noopener noreferrer" } },
      }),
      TextAlign.configure({ types: ["heading", "paragraph"], alignments: ["left", "center", "right", "justify"] }),
      Image.configure({ allowBase64: false }),
      Placeholder.configure({ placeholder: "Write your article..." }),
    ],
    content: value || "<p></p>",
    onUpdate: ({ editor: current }) => onChangeRef.current(current.getHTML()),
    onTransaction: () => setRevision(revision => revision + 1),
  });

  useEffect(() => { editor?.setEditable(!disabled); }, [disabled, editor]);
  useEffect(() => {
    if (editor && mode === "rich" && editor.getHTML() !== value) editor.commands.setContent(value || "<p></p>", { emitUpdate: false });
  }, [editor, mode, value]);

  function switchMode(next: "rich" | "source") {
    if (next === "rich" && editor) editor.commands.setContent(value || "<p></p>", { emitUpdate: false });
    setMode(next);
  }

  const words = (editor?.getText() ?? value.replace(/<[^>]+>/g, " ")).trim().split(/\s+/u).filter(Boolean).length;
  return <div className="overflow-hidden rounded-md border border-slate-300 bg-white focus-within:border-sky-600 focus-within:ring-2 focus-within:ring-sky-100">
    <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 bg-slate-50 px-2 py-2">
      <div className="flex flex-wrap gap-1" role="toolbar" aria-label="Article formatting">
        {mode === "rich" && editor && <>
          <Tool title="Paragraph" active={editor.isActive("paragraph")} onClick={() => editor.chain().focus().setParagraph().run()}><Pilcrow /></Tool>
          <Tool title="Heading 1" active={editor.isActive("heading", { level: 1 })} onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}><Heading1 /></Tool>
          <Tool title="Heading 2" active={editor.isActive("heading", { level: 2 })} onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}><Heading2 /></Tool>
          <Tool title="Heading 3" active={editor.isActive("heading", { level: 3 })} onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}><Heading3 /></Tool>
          <Divider />
          <Tool title="Bold" active={editor.isActive("bold")} onClick={() => editor.chain().focus().toggleBold().run()}><Bold /></Tool>
          <Tool title="Italic" active={editor.isActive("italic")} onClick={() => editor.chain().focus().toggleItalic().run()}><Italic /></Tool>
          <Tool title="Underline" active={editor.isActive("underline")} onClick={() => editor.chain().focus().toggleUnderline().run()}><Underline /></Tool>
          <Tool title="Strikethrough" active={editor.isActive("strike")} onClick={() => editor.chain().focus().toggleStrike().run()}><Strikethrough /></Tool>
          <Tool title="Inline code" active={editor.isActive("code")} onClick={() => editor.chain().focus().toggleCode().run()}><Code /></Tool>
          <Tool title="Clear formatting" onClick={() => editor.chain().focus().unsetAllMarks().clearNodes().run()}><RemoveFormatting /></Tool>
          <Divider />
          <Tool title="Insert link" active={editor.isActive("link")} onClick={() => setDialog("link")}><LinkIcon /></Tool>
          <Tool title="Insert image" onClick={() => setDialog("image")}><ImagePlus /></Tool>
          <Tool title="Bullet list" active={editor.isActive("bulletList")} onClick={() => editor.chain().focus().toggleBulletList().run()}><List /></Tool>
          <Tool title="Ordered list" active={editor.isActive("orderedList")} onClick={() => editor.chain().focus().toggleOrderedList().run()}><ListOrdered /></Tool>
          <Tool title="Blockquote" active={editor.isActive("blockquote")} onClick={() => editor.chain().focus().toggleBlockquote().run()}><Quote /></Tool>
          <Tool title="Code block" active={editor.isActive("codeBlock")} onClick={() => editor.chain().focus().toggleCodeBlock().run()}><Braces /></Tool>
          <Tool title="Horizontal rule" onClick={() => editor.chain().focus().setHorizontalRule().run()}><Minus /></Tool>
          <Divider />
          <Tool title="Align left" active={editor.isActive({ textAlign: "left" })} onClick={() => editor.chain().focus().setTextAlign("left").run()}><AlignLeft /></Tool>
          <Tool title="Align center" active={editor.isActive({ textAlign: "center" })} onClick={() => editor.chain().focus().setTextAlign("center").run()}><AlignCenter /></Tool>
          <Tool title="Align right" active={editor.isActive({ textAlign: "right" })} onClick={() => editor.chain().focus().setTextAlign("right").run()}><AlignRight /></Tool>
          <Tool title="Justify" active={editor.isActive({ textAlign: "justify" })} onClick={() => editor.chain().focus().setTextAlign("justify").run()}><AlignJustify /></Tool>
          <Divider />
          <Tool title="Undo" disabled={!editor.can().undo()} onClick={() => editor.chain().focus().undo().run()}><Undo2 /></Tool>
          <Tool title="Redo" disabled={!editor.can().redo()} onClick={() => editor.chain().focus().redo().run()}><Redo2 /></Tool>
        </>}
      </div>
      <div className="inline-flex rounded-md bg-slate-200 p-0.5" aria-label="Editor mode">
        <ModeButton active={mode === "rich"} onClick={() => switchMode("rich")}>Rich text</ModeButton>
        <ModeButton active={mode === "source"} onClick={() => switchMode("source")}>HTML</ModeButton>
      </div>
    </div>
    {mode === "rich" ? <EditorContent editor={editor} className="article-editor min-h-[28rem]" /> : <textarea aria-label="Article HTML source" className="min-h-[28rem] w-full resize-y border-0 bg-slate-950 p-5 font-mono text-sm leading-6 text-slate-100 outline-none" value={value} disabled={disabled} onChange={event => onChange(event.target.value)} spellCheck={false} />}
    <div className="flex items-center justify-between border-t border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-500"><span>{mode === "source" ? "HTML source" : "Rich text"}</span><span>{words} {words === 1 ? "word" : "words"} · {value.length.toLocaleString()} characters</span></div>
    {dialog === "link" && editor && <LinkDialog editor={editor} onClose={() => setDialog(null)} />}
    {dialog === "image" && editor && <ImageDialog editor={editor} onClose={() => setDialog(null)} />}
  </div>;
}

function Tool({ title, active, disabled, onClick, children }: { title: string; active?: boolean; disabled?: boolean; onClick: () => void; children: ReactNode }) {
  return <button type="button" title={title} aria-label={title} aria-pressed={active} disabled={disabled} onClick={onClick} className={`grid size-9 shrink-0 place-items-center rounded focus:outline-none focus:ring-2 focus:ring-sky-600 disabled:opacity-35 ${active ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-white hover:text-slate-950"}`}><span className="[&>svg]:size-4">{children}</span></button>;
}
function Divider() { return <span className="mx-0.5 h-7 w-px self-center bg-slate-300" aria-hidden="true" />; }
function ModeButton({ active, onClick, children }: { active: boolean; onClick: () => void; children: ReactNode }) { return <button type="button" onClick={onClick} className={`rounded px-2.5 py-1.5 text-xs font-semibold ${active ? "bg-white text-slate-950 shadow-sm" : "text-slate-600 hover:text-slate-950"}`}>{children}</button>; }

function LinkDialog({ editor, onClose }: { editor: NonNullable<ReturnType<typeof useEditor>>; onClose: () => void }) {
  const selected = editor.state.doc.textBetween(editor.state.selection.from, editor.state.selection.to, " ");
  const current = editor.getAttributes("link") as { href?: string; target?: string };
  const [error, setError] = useState("");
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const form = new FormData(event.currentTarget);
    const href = String(form.get("url") ?? "").trim(); const text = String(form.get("text") ?? "").trim();
    if (!validArticleUrl(href, "link")) { setError("Use an HTTP, HTTPS, or mailto URL."); return; }
    const attrs = { href, target: form.get("newTab") === "on" ? "_blank" : null };
    if (editor.state.selection.empty && text) editor.chain().focus().insertContent({ type: "text", text, marks: [{ type: "link", attrs }] }).run();
    else editor.chain().focus().extendMarkRange("link").setLink(attrs).run();
    onClose();
  }
  return <EditorDialog title="Insert link" onClose={onClose}><form onSubmit={submit} className="grid gap-4"><label className="grid gap-1.5 text-sm font-medium">URL<input name="url" className={fieldClass} defaultValue={current.href} placeholder="https://example.com" autoFocus required /></label><label className="grid gap-1.5 text-sm font-medium">Text<input name="text" className={fieldClass} defaultValue={selected} /></label><label className="flex min-h-10 items-center gap-2 text-sm"><input name="newTab" type="checkbox" defaultChecked={current.target === "_blank"} className="size-4" />Open in new tab</label>{error && <p className="text-sm text-red-700" role="alert">{error}</p>}<div className="flex justify-end gap-2"><button type="button" className={secondaryButton} onClick={onClose}>Cancel</button><button className={primaryButton}>Insert link</button></div></form></EditorDialog>;
}

function ImageDialog({ editor, onClose }: { editor: NonNullable<ReturnType<typeof useEditor>>; onClose: () => void }) {
  const [error, setError] = useState("");
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const form = new FormData(event.currentTarget); const src = String(form.get("url") ?? "").trim();
    if (!validArticleUrl(src, "image")) { setError("Use an HTTP or HTTPS image URL."); return; }
    editor.chain().focus().setImage({ src, alt: String(form.get("alt") ?? "").trim(), title: String(form.get("title") ?? "").trim() }).run(); onClose();
  }
  return <EditorDialog title="Insert image" onClose={onClose}><form onSubmit={submit} className="grid gap-4"><label className="grid gap-1.5 text-sm font-medium">Image URL<input name="url" className={fieldClass} placeholder="https://images.example.com/article.jpg" autoFocus required /></label><label className="grid gap-1.5 text-sm font-medium">Alternative text<input name="alt" className={fieldClass} required /></label><label className="grid gap-1.5 text-sm font-medium">Title<input name="title" className={fieldClass} /></label>{error && <p className="text-sm text-red-700" role="alert">{error}</p>}<div className="flex justify-end gap-2"><button type="button" className={secondaryButton} onClick={onClose}>Cancel</button><button className={primaryButton}>Insert image</button></div></form></EditorDialog>;
}

function EditorDialog({ title, onClose, children }: { title: string; onClose: () => void; children: ReactNode }) {
  return <div className="fixed inset-0 z-[75] grid place-items-center bg-slate-950/45 p-4" role="presentation"><section role="dialog" aria-modal="true" aria-labelledby="editor-dialog-title" className="w-full max-w-lg rounded-md bg-white p-5 shadow-2xl"><div className="mb-5 flex items-center justify-between"><h2 id="editor-dialog-title" className="text-lg font-semibold">{title}</h2><button type="button" title="Close" aria-label="Close" onClick={onClose} className="rounded p-2 text-slate-500 hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-600"><X className="size-5" /></button></div>{children}</section></div>;
}
