import os
import glob
from datetime import datetime
import speech_recognition as sr
from pydub import AudioSegment
import logging

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


async def download_voice_message(voice_file, file_path):
    """Download voice message from Telegram."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    logger.info(f"Downloading voice message to {file_path}")
    await voice_file.download_to_drive(file_path)
    logger.info(f"Voice message downloaded successfully")

    # Convert to text and save transcription right away
    logger.info(f"Starting transcription for {file_path}")
    transcription = transcribe_audio(file_path)

    # Save transcription alongside audio file
    text_path = file_path.replace(".ogg", ".txt")
    with open(text_path, "w", encoding="utf-8") as f:
        f.write(transcription)

    logger.info(f"Transcription saved to {text_path}")
    return file_path


def transcribe_audio(audio_file_path):
    """Convert audio to text using SpeechRecognition."""
    try:
        # Get file size
        file_size = os.path.getsize(audio_file_path) / (1024 * 1024)  # Size in MB
        logger.info(f"Processing audio file of size: {file_size:.2f} MB")

        # Convert from OGG to WAV
        logger.info("Converting OGG to WAV...")
        audio = AudioSegment.from_ogg(audio_file_path)
        wav_path = audio_file_path.replace(".ogg", ".wav")
        audio.export(wav_path, format="wav")
        logger.info("Conversion complete")

        # For long audio files, split into chunks
        if file_size > 10:  # If greater than 10 MB
            logger.info("Large audio file detected, processing in chunks...")
            return transcribe_large_audio(wav_path)

        # Use SpeechRecognition to transcribe
        logger.info("Starting speech recognition...")
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            logger.info("Audio recorded, sending to Google Speech Recognition...")
            text = recognizer.recognize_google(audio_data)

        # Remove temporary WAV file
        os.remove(wav_path)

        # Add timestamp to the transcription
        timestamp = datetime.fromtimestamp(os.path.getmtime(audio_file_path))
        formatted_timestamp = timestamp.strftime("%I:%M %p")
        transcription = f"[{formatted_timestamp}] {text}"

        logger.info(f"Transcribed: {transcription[:50]}...")
        return transcription

    except sr.UnknownValueError:
        logger.error(f"Google Speech Recognition could not understand audio")
        return f"[Transcription failed] Error: Speech not recognized"

    except sr.RequestError as e:
        logger.error(
            f"Could not request results from Google Speech Recognition service: {str(e)}"
        )
        return f"[Transcription failed] Error: Could not connect to recognition service"

    except Exception as e:
        logger.error(f"Error transcribing {audio_file_path}: {str(e)}")
        return f"[Transcription failed] Error: {str(e)}"


def transcribe_large_audio(wav_path):
    """Transcribe large audio files by splitting them into chunks."""
    try:
        logger.info("Loading audio file...")
        audio = AudioSegment.from_wav(wav_path)
        logger.info(f"Audio duration: {len(audio)/1000:.2f} seconds")

        # Split audio into 30-second chunks
        chunk_length_ms = 30000  # 30 seconds
        chunks = [
            audio[i : i + chunk_length_ms]
            for i in range(0, len(audio), chunk_length_ms)
        ]
        logger.info(f"Split audio into {len(chunks)} chunks")

        # Process each chunk
        transcription_parts = []
        recognizer = sr.Recognizer()

        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)}...")
            # Export chunk to temporary file
            chunk_path = f"temp_audio/chunk_{i}.wav"
            chunk.export(chunk_path, format="wav")

            # Transcribe chunk
            with sr.AudioFile(chunk_path) as source:
                audio_data = recognizer.record(source)
                try:
                    part_text = recognizer.recognize_google(audio_data)
                    transcription_parts.append(part_text)
                    logger.info(f"Chunk {i+1} transcribed: {part_text[:30]}...")
                except sr.UnknownValueError:
                    logger.warning(f"Chunk {i+1}: Speech not recognized")
                except sr.RequestError as e:
                    logger.error(f"Chunk {i+1}: Request error - {str(e)}")
                except Exception as e:
                    logger.error(f"Chunk {i+1}: Error - {str(e)}")

            # Remove temporary chunk file
            try:
                os.remove(chunk_path)
            except:
                pass

        # Remove main WAV file
        try:
            os.remove(wav_path)
        except:
            pass

        # Combine all parts
        full_text = " ".join(transcription_parts)
        logger.info(
            f"Full transcription complete, total length: {len(full_text)} characters"
        )

        # Add timestamp
        timestamp = datetime.now().strftime("%I:%M %p")
        transcription = f"[{timestamp}] {full_text}"

        return transcription

    except Exception as e:
        logger.error(f"Error in large file transcription: {str(e)}")
        return f"[Transcription failed] Error in large file processing: {str(e)}"


def get_daily_transcriptions(date_str, count_only=False):
    """Get all transcriptions for a specific date."""
    pattern = f"temp_audio/{date_str}_*.txt"
    transcription_files = sorted(glob.glob(pattern))

    if count_only:
        return len(transcription_files)

    transcriptions = []
    for file_path in transcription_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content.startswith("[Transcription failed]"):
                    logger.warning(f"Including failed transcription: {file_path}")
                transcriptions.append(content)
        except Exception as e:
            logger.error(f"Error reading {file_path}: {str(e)}")

    logger.info(f"Retrieved {len(transcriptions)} transcriptions for {date_str}")
    return transcriptions


def clear_daily_files(date_str):
    """Clear processed files for a specific date."""
    pattern = f"temp_audio/{date_str}_*"
    files = glob.glob(pattern)

    for file_path in files:
        try:
            os.remove(file_path)
            logger.info(f"Removed file: {file_path}")
        except Exception as e:
            logger.error(f"Error removing {file_path}: {str(e)}")
