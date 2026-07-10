import { useState, useRef } from 'react'
import { Upload, Download, Sparkles, Image, Eraser } from 'lucide-react'
import { api } from '../api'

export default function PhotoEnhance() {
  const [original, setOriginal] = useState<string | null>(null)
  const [enhanced, setEnhanced] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [removeBg, setRemoveBg] = useState(false)
  const [filename, setFilename] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFile = async (file: File) => {
    setOriginal(URL.createObjectURL(file))
    setEnhanced(null)
    setLoading(true)
    try {
      const res = await api.enhancePhoto(file, removeBg)
      setFilename(res.filename)
      setEnhanced(`http://127.0.0.1:8420/api/photos/${res.filename}`)
    } finally { setLoading(false) }
  }

  return (
    <div className="p-8 max-w-4xl mx-auto animate-fade-in">
      <div className="mb-8">
        <h1 className="page-title">AI Photo Studio</h1>
        <p className="page-subtitle">Photos professionnelles pour vos annonces Vinted</p>
      </div>

      <div className="glass-card border-2 border-dashed border-gray-200 p-12 text-center cursor-pointer hover:border-gray-300 transition-colors mb-6"
        onClick={() => inputRef.current?.click()}
        onDragOver={e => e.preventDefault()}
        onDrop={e => { e.preventDefault(); const f = e.dataTransfer.files[0]; if (f) handleFile(f) }}>
        <Upload className="w-10 h-10 text-gray-300 mx-auto mb-3" />
        <p className="text-gray-500">Glissez une photo ou cliquez pour importer</p>
        <p className="text-xs text-gray-400 mt-1">JPG, PNG — photo de vêtement</p>
        <input ref={inputRef} type="file" accept="image/*" className="hidden"
          onChange={e => { const f = e.target.files?.[0]; if (f) handleFile(f) }} />
      </div>

      <div className="flex items-center gap-3 mb-6">
        <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
          <input type="checkbox" checked={removeBg} onChange={e => setRemoveBg(e.target.checked)}
            className="rounded border-gray-300" />
          <Eraser className="w-4 h-4" />Supprimer l'arrière-plan
        </label>
      </div>

      {(original || enhanced) && (
        <div className="grid grid-cols-2 gap-6">
          <div>
            <p className="text-sm text-gray-500 mb-2 flex items-center gap-2"><Image className="w-4 h-4" />Original</p>
            {original && <img src={original} alt="" className="rounded-2xl w-full shadow-sm" />}
          </div>
          <div>
            <p className="text-sm text-gray-500 mb-2 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-violet-500" />
              Amélioré {loading && <span className="text-violet-500 animate-pulse">en cours...</span>}
            </p>
            {enhanced && <img src={enhanced} alt="" className="rounded-2xl w-full shadow-sm" />}
          </div>
        </div>
      )}

      {enhanced && (
        <button onClick={() => { const a = document.createElement('a'); a.href = enhanced; a.download = filename; a.click() }}
          className="btn-primary mt-6">
          <Download className="w-4 h-4" />Télécharger la photo
        </button>
      )}

      <div className="glass-card mt-6">
        <h3 className="font-medium text-sm mb-3">Améliorations appliquées</h3>
        <div className="grid grid-cols-2 gap-2 text-sm text-gray-600">
          <span>✓ Luminosité et exposition</span>
          <span>✓ Netteté et clarté</span>
          <span>✓ Contraste subtil</span>
          <span>✓ Réduction du bruit</span>
          <span>✓ Arrière-plan nettoyé (option)</span>
          <span>✗ Pas de modification des couleurs du vêtement</span>
        </div>
      </div>
    </div>
  )
}
