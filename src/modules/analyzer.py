"""
Módulo de Análise Viral (Stage 3)
Usa Gemini AI para análise inteligente de momentos virais
"""
from typing import List, Dict, Optional
from pathlib import Path
import re
import os
import json
from ..core.config import Config
from ..core.logger import setup_logger

logger = setup_logger(__name__)

# Tentar importar Gemini
GEMINI_AVAILABLE = False
try:
# import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    logger.warning("google-generativeai não instalado.")


class ViralAnalyzer:
    """Analisa transcrição usando Gemini AI para identificar momentos virais"""

    def __init__(self):
        self.gemini_client = None
        api_key = os.getenv("GEMINI_API_KEY")

        if GEMINI_AVAILABLE and api_key:
            try:
                genai.configure(api_key=api_key)
                self.gemini_client = genai.GenerativeModel('gemini-1.5-flash')
                logger.info("🔍 Analisador Viral: ONLINE (Gemini 1.5 Flash)")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao conectar Gemini: {e}")
        else:
            logger.info("🔍 Analisador Viral: Modo Offline (Keywords Locais)")

        # Palavras-chave virais (fallback)
        self.viral_keywords = {
            'dinheiro': ['dinheiro', 'real', 'reais', 'mil', 'milhão', 'rico', 'renda', 'ganhar', 'lucro', 'faturar'],
            'segredo': ['segredo', 'verdade', 'ninguém', 'escondido', 'revelar', 'descobri'],
            'urgência': ['agora', 'hoje', 'rápido', 'urgente', 'última chance', 'corre'],
            'polêmica': ['polêmica', 'controverso', 'chocante', 'absurdo', 'inacreditável', 'mentira'],
            'sucesso': ['sucesso', 'vitória', 'conquista', 'resultado', 'transformação', 'mudou'],
            'erro': ['erro', 'errado', 'falha', 'problema', 'armadilha', 'cuidado'],
            'emoção': ['amor', 'medo', 'raiva', 'feliz', 'triste', 'chorar', 'incrível']
        }

    def analyze_transcript(
        self,
        segments: List[Dict],
        emotion_peaks: Optional[List[Dict]] = None,
        min_duration: int = 30,
        max_duration: int = 60,
        required_count: int = 3
    ) -> List[Dict]:
        """
        Analisa transcrição e identifica momentos virais usando abordagem Híbrida.
        """
        from ..core.hybrid_ai import HybridAI
        hybrid = HybridAI()

        results = hybrid.call(
            local_func=lambda: self._analyze_locally(segments, emotion_peaks, min_duration, max_duration, required_count),
            gemini_func=lambda: self._analyze_with_gemini(segments, emotion_peaks, min_duration, max_duration) if self.gemini_client else None,
            task_name="Viral Analysis"
        )

        return self._enforce_strict_duration(results, segments, min_duration)

    def _analyze_with_gemini(
        self,
        segments: List[Dict],
        emotion_peaks: Optional[List[Dict]] = None,
        min_duration: int = 30,
        max_duration: int = 60
    ) -> List[Dict]:
        """Análise usando Gemini AI"""
        logger.info("   🧠 Usando Gemini AI para análise profunda...")

        # Preparar texto completo com timestamps
        full_text = ""
        for seg in segments:
            full_text += f"[{seg['start']:.1f}s - {seg['end']:.1f}s]: {seg['text']}\n"

        # Limitar tamanho
        if len(full_text) > 10000:
            full_text = full_text[:10000] + "\n... (texto truncado)"

        prompt = f"""
Você é um especialista em conteúdo viral para TikTok, Reels e Shorts.

Analise esta transcrição de vídeo e identifique os 5 MELHORES momentos para criar clips virais curtos ({min_duration}-{max_duration} segundos).

TRANSCRIÇÃO COM TIMESTAMPS:
{full_text}

CRITÉRIOS DE VIRALIDADE (em ordem de importância):
1. HOOK FORTE - Primeiros 3 segundos capturam atenção imediatamente
2. EMOÇÃO - Momentos que causam reação emocional (surpresa, riso, motivação)
3. VALOR - Conteúdo que ensina algo útil ou revela segredo
4. CONTROVERSO - Opiniões fortes ou afirmações polêmicas
5. NÚMEROS - Dados específicos que impressionam
6. HISTÓRIA - Mini-narrativas com início, meio e fim

RESPONDA EM JSON (SOMENTE JSON, sem markdown):
{{
    "viral_moments": [
        {{
            "start": 125.0,
            "end": 170.0,
            "score": 9.5,
            "hook": "A frase de abertura mais impactante para o clip",
            "reason": "Por que esse momento é viral",
            "keywords": ["keyword1", "keyword2"],
            "emotion": "qual emoção principal",
            "viral_potential": "alto/médio/baixo",
            "suggested_title": "Título viral para o clip"
        }}
    ],
    "overall_analysis": {{
        "main_topic": "tema principal do vídeo",
        "target_audience": "para quem é esse conteúdo",
        "best_platform": "TikTok/Reels/Shorts",
        "content_quality": 0-10
    }}
}}
"""

        response = self.gemini_client.generate_content(prompt)
        text = response.text

        # Limpar resposta (remover markdown se presente)
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            logger.warning("Resposta do Gemini não é JSON válido, usando fallback")
            return self._analyze_locally(segments, emotion_peaks)

        # Processar momentos
        viral_moments = []
        for moment in data.get('viral_moments', []):
            viral_moments.append({
                'start': moment.get('start', 0),
                'end': moment.get('end', 0),
                'score': moment.get('score', 5.0),
                'hook': moment.get('hook', ''),
                'reason': moment.get('reason', ''),
                'keywords': moment.get('keywords', []),
                'emotion_intensity': 0.8 if moment.get('viral_potential') == 'alto' else 0.5,
                'text_preview': moment.get('suggested_title', ''),
                'gemini_analysis': True
            })

        # Ordenar por score
        viral_moments.sort(key=lambda x: x['score'], reverse=True)

        logger.info(f"✅ Gemini identificou {len(viral_moments)} momentos virais")

        # Log análise geral
        overall = data.get('overall_analysis', {})
        if overall:
            logger.info(f"   Tema: {overall.get('main_topic', 'N/A')}")
            logger.info(f"   Qualidade: {overall.get('content_quality', 'N/A')}/10")

        return viral_moments

    def _analyze_locally(
        self,
        segments: List[Dict],
        emotion_peaks: Optional[List[Dict]] = None,
        min_duration: int = 30,
        max_duration: int = 60,
        required_count: int = 3
    ) -> List[Dict]:
        """Análise usando keywords locais com Threshold Dinâmico"""
        logger.info(f"   📝 Usando análise local (duração: {min_duration}-{max_duration}s)...")

        viral_moments = []
        clip_min = min_duration
        clip_max = max_duration

        # Gerar lista de durações para testar (ex: min, média, max)
        durations = sorted(list(set([min_duration, (min_duration + max_duration) // 2, max_duration])))

        # Threshold inicial
        min_score = 6.0
        
        # Loop de tentativas (reduz threshold se não encontrar o suficiente)
        for attempt in range(3):
            viral_moments = []
            logger.info(f"   🔍 Tentativa {attempt+1}: Buscando clips com score >= {min_score}")
            
            for i, segment in enumerate(segments):
                start_time = segment['start']

                for duration in durations:
                    if duration < clip_min or duration > clip_max:
                        continue

                    end_time = start_time + duration
                    clip_text = self._get_text_in_range(segments, start_time, end_time)

                    if not clip_text:
                        continue

                    score_data = self._calculate_viral_score(
                        clip_text, start_time, end_time, emotion_peaks
                    )

                    if score_data['score'] >= min_score:
                        viral_moments.append({
                            'start': start_time,
                            'end': end_time,
                            'score': score_data['score'],
                            'hook': self._generate_hook(clip_text),
                            'reason': score_data['reason'],
                            'keywords': score_data['keywords'],
                            'emotion_intensity': score_data['emotion_intensity'],
                            'text_preview': clip_text[:100] + '...',
                            'gemini_analysis': False
                        })

            viral_moments.sort(key=lambda x: x['score'], reverse=True)
            viral_moments = self._remove_overlaps(viral_moments)
            
            # Se encontrou o suficiente, para
            if len(viral_moments) >= required_count:
                break
            
            # Senão, reduz threshold
            min_score -= 1.0
            if min_score < 3.0: break # Limite mínimo de dignidade

        logger.info(f"✅ {len(viral_moments)} momentos virais identificados (local)")
        
        # Retornar TOP N se houver muitos
        if len(viral_moments) > required_count * 2:
             return viral_moments[:required_count * 2]

        return viral_moments

    def _get_text_in_range(self, segments: List[Dict], start: float, end: float) -> str:
        """Extrai texto dentro de um intervalo de tempo"""
        texts = []
        for seg in segments:
            if seg['start'] >= start and seg['end'] <= end:
                texts.append(seg['text'])
            elif seg['start'] < end and seg['end'] > start:
                texts.append(seg['text'])
        return ' '.join(texts)

    def _calculate_viral_score(
        self,
        text: str,
        start: float,
        end: float,
        emotion_peaks: Optional[List[Dict]] = None
    ) -> Dict:
        """Calcula score viral de um trecho"""
        score = 5.0
        reasons = []
        found_keywords = []
        text_lower = text.lower()

        # Análise de palavras-chave
        keyword_score = 0
        for category, keywords in self.viral_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    keyword_score += 0.5
                    found_keywords.append(keyword)
                    if keyword_score == 0.5:
                        reasons.append(f"Palavra viral: {category}")

        score += min(keyword_score, 3.0)

        # Números
        numbers = re.findall(r'\d+(?:\.\d+)?', text)
        if numbers:
            score += 1.0
            reasons.append("Números específicos")

        # Perguntas
        if '?' in text or any(word in text_lower for word in ['como', 'por que', 'qual']):
            score += 0.5
            reasons.append("Pergunta")

        # Emoção do áudio
        emotion_intensity = 0.0
        if emotion_peaks:
            peaks_in_range = [p for p in emotion_peaks if start <= p['timestamp'] <= end]
            if peaks_in_range:
                emotion_intensity = sum(p['intensity'] for p in peaks_in_range) / len(peaks_in_range)
                score += emotion_intensity * 2.0
                reasons.append(f"Picos emocionais ({len(peaks_in_range)})")

        # Início forte
        first_words = text_lower.split()[:5]
        strong_starts = ['olha', 'cuidado', 'atenção', 'nunca', 'sempre', 'todo', 'ninguém', 'para']
        if any(word in first_words for word in strong_starts):
            score += 1.0
            reasons.append("Início forte")

        return {
            'score': round(min(score, 10.0), 1),
            'reason': ' | '.join(reasons) if reasons else 'Análise padrão',
            'keywords': list(set(found_keywords)),
            'emotion_intensity': emotion_intensity
        }

    def _generate_hook(self, text: str) -> str:
        """Gera um hook viral para o clipe"""
        sentences = text.split('.')
        first_sentence = sentences[0].strip()

        if len(first_sentence) > 60:
            hook = first_sentence[:57] + '...'
        else:
            hook = first_sentence

        hook = hook.capitalize()

        text_lower = text.lower()
        if any(word in text_lower for word in ['dinheiro', 'rico', 'mil']):
            hook = '💰 ' + hook
        elif any(word in text_lower for word in ['segredo', 'verdade']):
            hook = '🔥 ' + hook
        elif any(word in text_lower for word in ['cuidado', 'erro', 'armadilha']):
            hook = '⚠️ ' + hook
        elif any(word in text_lower for word in ['incrível', 'chocante']):
            hook = '😱 ' + hook

        return hook

    def _remove_overlaps(self, moments: List[Dict], min_gap: float = 10.0) -> List[Dict]:
        """Remove momentos sobrepostos"""
        if not moments:
            return []

        filtered = [moments[0]]
        for moment in moments[1:]:
            last = filtered[-1]
            if moment['start'] >= last['end'] - min_gap: # Permite um pequeno overlap, mas prioriza novos trechos
                 # Se o overlap for pequeno (ex: 5s), permite para capturar conteúdo adjacente
                 if moment['start'] >= last['end']:
                    filtered.append(moment)
                 # Se overlap for grande, ignora

        return filtered

    def _enforce_strict_duration(self, moments: List[Dict], segments: List[Dict], min_duration: int) -> List[Dict]:
        """GARANTE que nenhum clip tenha menos que min_duration (ex: 60s)"""
        if not moments or not segments:
            return moments
            
        video_duration = segments[-1]['end']
        
        for m in moments:
            duration = m['end'] - m['start']
            
            if duration < min_duration:
                # Precisa estender
                diff = min_duration - duration
                
                # Tenta estender simetricamente (metade pra cada lado)
                extend_start = diff / 2
                extend_end = diff / 2
                
                # Ajusta start
                new_start = m['start'] - extend_start
                if new_start < 0:
                    # Se bater no 0, joga o excesso pro final
                    extend_end += (0 - new_start)
                    new_start = 0
                
                # Ajusta end
                new_end = m['end'] + extend_end
                
                # Se bater no final do video (improvável mas possível)
                if new_end > video_duration:
                    # Tenta compensar voltando o start (se possível)
                    excess = new_end - video_duration
                    new_end = video_duration
                    new_start = max(0, new_start - excess) # Garante que start não fique negativo
                
                # Aplica
                m['start'] = new_start
                m['end'] = new_end
                
                logger.info(f"   ⚠️ Clip estendido para {min_duration}s: {m['start']:.1f}s - {m['end']:.1f}s (Original: {duration:.1f}s)")

        return moments
