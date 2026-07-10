import { useState, useRef } from 'react'
import { Upload, Download, Sparkles, Image, Eraser, Copy, CheckCircle, Wand2 } from 'lucide-react'
import { api, getApiBase } from '../api'

const VINTED_PREMIUM_PROMPT = `Transform this clothing photo into a professional, premium-quality product image for a high-end fashion marketplace.

Keep the exact same clothing item, preserving the original design, colors, patterns, logos, materials, and details. Do not change the identity of the garment.

Improve the photo with realistic professional studio lighting, soft natural shadows, balanced exposure, and a clean premium atmosphere.

Make the clothing look:
* perfectly clean;
* smooth and well presented;
* naturally ironed and wrinkle-free while keeping realistic fabric texture;
* high quality and attractive;
* professionally photographed.

Enhance the fabric details, stitching, texture, and quality without making the item look fake.

Create a beautiful minimalist background suitable for a luxury clothing listing:
* clean;
* bright;
* modern;
* elegant;
* realistic.

Make the composition look like a professional fashion product shoot from a premium clothing brand.

Improve:
* sharpness;
* lighting;
* contrast;
* colors;
* overall image quality.

The result should look like it was taken with a professional camera in a fashion studio, while remaining completely realistic and faithful to the original item.

Do not:
* change the clothing model;
* add or remove logos;
* modify the colors;
* create fake details;
* make the item look different from reality.

The final image should be a realistic, premium, attractive clothing photo optimized for selling online.`

export default function PhotoEnhance() {
  const [original, setOriginal] = useState<string | null>(null)
  const [enhanced, setEnhanced] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [removeBg, setRemoveBg] = useState(false)
  const [filename, setFilename] = useState('')
  const [copied, setCopied] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const apiBase = getApiBase().replace('/api', '')

  const handleFile = async (file: File) => {
    setOriginal(URL.createObjectURL(file))
    setEnhanced(null)
    setLoading(true)
    try {
      const res = await api.enhancePhoto(file, removeBg)
      setFilename(res.filename)
      setEnhanced(`${apiBase}/api/photos/${res.filename}`)
    } finally { setLoading(false) }
  }

  const copyPrompt = () => {
    navigator.clipboard.writeText(VINTED_PREMIUM_PROMPT)
    setCopied(true)
    setTimeout(() => setCopied(false), 2500)
  }

  return (
    <div className="p-4 md:p-8 max-w-5xl mx-auto animate-fade-in">
      <div className="mb-8">
        <h1 className="page-title">AI Photo Studio</h1>
        <p className="page-subtitle">Amélioration locale + prompts IA image professionnels</p>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Upload & enhance */}
        <div className="space-y-4">
          <div className="glass-card border-2 border-dashed border-slate-200 p-10 text-center cursor-pointer hover:border-violet-300 transition-colors"
            onClick={() => inputRef.current?.click()}
            onDragOver={e => e.preventDefault()}
            onDrop={e => { e.preventDefault(); const f = e.dataTransfer.files[0]; if (f) handleFile(f) }}>
            <Upload className="w-10 h-10 text-slate-300 mx-auto mb-3" />
            <p className="text-slate-600 font-medium">Glissez une photo ou cliquez</p>
            <p className="text-xs text-slate-400 mt-1">JPG, PNG — photo de vêtement</p>
            <input ref={inputRef} type="file" accept="image/*" className="hidden"
              onChange={e => { const f = e.target.files?.[0]; if (f) handleFile(f) }} />
          </div>

          <div className="glass-card">
            <label className="flex items-center gap-2 text-sm text-slate-600 cursor-pointer">
              <input type="checkbox" checked={removeBg} onChange={e => setRemoveBg(e.target.checked)}
                className="rounded border-slate-300" />
              <Eraser className="w-4 h-4" />Supprimer l'arrière-plan (amélioration locale)
            </label>
          </div>

          {(original || enhanced) && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-slate-500 mb-2 flex items-center gap-1"><Image className="w-3.5 h-3.5" />Original</p>
                {original && <img src={original} alt="" className="rounded-2xl w-full shadow-sm" />}
              </div>
              <div>
                <p className="text-xs text-slate-500 mb-2 flex items-center gap-1">
                  <Sparkles className="w-3.5 h-3.5 text-violet-500" />
                  Amélioré {loading && <span className="text-violet-500 animate-pulse">...</span>}
                </p>
                {enhanced && <img src={enhanced} alt="" className="rounded-2xl w-full shadow-sm" />}
              </div>
            </div>
          )}

          {enhanced && (
            <button onClick={() => { const a = document.createElement('a'); a.href = enhanced; a.download = filename; a.click() }}
              className="btn-primary w-full">
              <Download className="w-4 h-4" />Télécharger la photo améliorée
            </button>
          )}
        </div>

        {/* AI Prompt */}
        <div className="glass-card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold flex items-center gap-2">
              <Wand2 className="w-4 h-4 text-violet-500" />
              Prompt — Style Vinted Premium
            </h3>
            <button onClick={copyPrompt} className="btn-primary text-xs py-2">
              {copied ? <CheckCircle className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
              {copied ? 'Copié !' : 'Copier le prompt'}
            </button>
          </div>
          <p className="text-xs text-slate-500 mb-3">
            Collez ce prompt dans ChatGPT, Midjourney, DALL·E ou tout outil IA image avec votre photo.
          </p>
          <pre className="text-[11px] leading-relaxed text-slate-600 bg-slate-50 rounded-2xl p-4 max-h-[420px] overflow-y-auto whitespace-pre-wrap border border-slate-100">
            {VINTED_PREMIUM_PROMPT}
          </pre>
          <div className="mt-4 grid grid-cols-2 gap-2 text-xs text-slate-500">
            <span>✓ Éclairage studio</span>
            <span>✓ Fond minimaliste</span>
            <span>✓ Textures réalistes</span>
            <span>✓ Fidèle au vêtement</span>
          </div>
        </div>
      </div>
    </div>
  )
}
