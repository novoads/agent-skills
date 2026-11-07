#!/usr/bin/env python3
"""Does this source actually contain SPEECH? Free, local, and it runs before you spend.

    python3 check-speech.py <file> [--json]

Exit codes, which are the whole point of the script:

    0  speech        one talking voice is present. Safe to price and convert.
    2  no speech     no audio stream, silence, or audio that is not a talking
                     voice (a music bed, a room tone, an effects-only track).
                     REFUSE. Do not call the endpoint.
    3  unclear       the measurements disagree. Stop and have a human listen
                     before anything is charged.
    1  could not run ffmpeg/ffprobe missing, or the file could not be read.

WHY THIS EXISTS. `POST /v1/voice-changes` gates on "does this have an audio
track", not on "is anyone talking". Send it a music bed and it converts the music
into vocal noise, bills it like speech, and returns `200`. That is a
charged success, not an error, and no retry gets the credits back. This check is
free and takes about a second, so it runs first, every time.

HOW IT DECIDES. Two independent measurements, from voiceprint.measure():

  voicedFraction  the share of loud frames that are periodic in the human
                  speaking range (70-350 Hz). A talking voice is periodic almost
                  everywhere it is loud. A mix of instruments is not: the
                  autocorrelation peak jumps between notes and harmonics and
                  fails on a large minority of frames.
  f0Iqr           the interquartile spread of the detected pitch, in Hz. ONE
                  person's voice lives in a narrow band. Music does not.

Measured on 13 real files before the thresholds were chosen (2026-08-12). The
same set is tabulated in evals.md § C:

  a 15s UGC ad (speech + a glass-shatter effect)   voiced 0.93   iqr  27
  its speech span alone, from 2.2s                 voiced 0.96   iqr  26
  a re-voiced cut of the same ad                   voiced 0.91   iqr  18
  three synthesized voice-over takes, es and en    voiced 0.97-1.00  iqr 49-56
  a 5s UGC voice track                             voiced 0.99   iqr  33
  an 85s phone recording of one speaker            voiced 0.98   iqr  19
  the same ad's first 2.1s: effect, no speech      voiced 0.18   iqr  35
  an instrumental hip-hop track (full, and a 30s cut)  voiced 0.77-0.78  iqr 158-222
  an instrumental film cue (full, and a 30s cut)   voiced 0.48-0.49  iqr  58-212

So on that set every speech file sits at 0.91 or above and every non-speech file
at 0.78 or below. SPEECH_MIN is the midpoint of that gap rather than either edge,
and NOSPEECH_MAX is set well under it so the band between them is genuinely
"these do not agree, ask a human" and not a rounding error. The pitch-spread
ceiling is the second, independent test: it catches a polyphonic bed that happens
to score high on periodicity.

WHAT IT CANNOT DO, stated because a gate that oversells itself is worse than none:

* SUNG vocals read as speech. One singer is one periodic voice in the same range.
  A song sent to the endpoint converts and charges like any other source.
* A SUSTAINED SINGLE PITCH reads as speech: a drone, a synth pad, an organ note,
  a harmonic stack of tones. Those are exactly one periodic thing in the range,
  which is what this measures. The tell is in the output rather than the exit
  code -- a pitch spread near 0 Hz is a machine, not a person, and the narrowest
  real voice in the calibration set above is 18 Hz. No threshold is set on it
  here because 13 files is not enough to place one; read the reported spread.
* Narration OVER a music bed reads as speech, correctly -- but the endpoint
  converts the WHOLE track, bed included. Fence the bed in assembly, or convert a
  music-free cut of the audio.
* It measures a whole file. A source that is 30s of music followed by 4s of
  speech is a source with speech in it; use --json, read speechStart, and cut.
"""

import json
import shutil
import sys

import voiceprint

SPEECH_MIN_VOICED = 0.85
NOSPEECH_MAX_VOICED = 0.60
SPEECH_MAX_IQR = 80.0
NOSPEECH_MIN_IQR = 120.0


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    as_json = "--json" in argv
    if len(args) != 1:
        print(__doc__)
        return 1
    path = args[0]
    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            print(f"ERROR: {tool} is not on PATH. This check needs ffmpeg.")
            return 1
    try:
        voiceprint.require_readable(path)
    except voiceprint.Unreadable as exc:
        print(f"ERROR: {exc}")
        return 1

    if not voiceprint.has_audio_stream(path):
        return report({"verdict": "no-speech", "reason": "no audio stream at all",
                       "durationSeconds": voiceprint.duration_seconds(path)},
                      as_json, 2)
    try:
        m = voiceprint.measure(path)
    except voiceprint.NoAudio as exc:
        return report({"verdict": "no-speech", "reason": str(exc)}, as_json, 2)

    if m["framesMeasured"] == 0 or m["peakDb"] < -60:
        m.update(verdict="no-speech", reason="the track is silent")
        return report(m, as_json, 2)

    voiced, iqr = m["voicedFraction"], m["f0Iqr"]
    # A pitch is REQUIRED for a speech verdict, never for a refusal. Under four
    # voiced frames f0Median and f0Iqr stay at their 0.0 defaults, and 0.0
    # SATISFIES `iqr <= SPEECH_MAX_IQR` -- so without this term the answer was
    # "one periodic voice, pitch spread 0 Hz around 0 Hz" and exit 0, which
    # SKILL.md reads as "proceed" and whose reported pitch it calls the casting
    # brief's spine. match-voice.py refuses that same input outright, so the two
    # gates disagreed and the one authorizing a charge was the optimistic one.
    # It only ever removes an exit 0: a confident refusal still wins below.
    measured_pitch = m["f0Median"] > 0
    speechy = voiced >= SPEECH_MIN_VOICED and iqr <= SPEECH_MAX_IQR and measured_pitch
    not_speechy = voiced < NOSPEECH_MAX_VOICED or iqr > NOSPEECH_MIN_IQR

    if speechy and not not_speechy:
        m.update(verdict="speech",
                 reason=f"{voiced:.0%} of loud frames are one periodic voice, "
                        f"pitch spread {iqr:.0f} Hz around {m['f0Median']:.0f} Hz")
        code = 0
    elif not_speechy and not speechy:
        why = []
        if voiced < NOSPEECH_MAX_VOICED:
            why.append(f"only {voiced:.0%} of loud frames are periodic")
        if iqr > NOSPEECH_MIN_IQR:
            why.append(f"pitch jumps over {iqr:.0f} Hz, wider than one voice")
        m.update(verdict="no-speech", reason="; ".join(why))
        code = 2
    elif not measured_pitch:
        m.update(verdict="unclear",
                 reason="too few voiced frames to measure a pitch at all, so there is "
                        "no voice here to cast against; listen before spending")
        code = 3
    else:
        m.update(verdict="unclear",
                 reason=f"voiced {voiced:.2f} and pitch spread {iqr:.0f} Hz do not "
                        "agree; listen to the source before spending")
        code = 3
    return report(m, as_json, code)


def report(m, as_json, code):
    if as_json:
        print(json.dumps(m, indent=2))
        return code
    verdict = m["verdict"].upper()
    print(f"{verdict}: {m['reason']}")
    if code != 2 and m.get("speechStart") is not None:
        print(f"  speech runs {m['speechStart']:.2f}s to {m['speechEnd']:.2f}s "
              f"of {m['durationSeconds']:.2f}s")
    if m.get("f0Median"):
        print(f"  source voice pitch: median {m['f0Median']:.0f} Hz, "
              f"IQR {m['f0Q1']:.0f}-{m['f0Q3']:.0f} Hz")
    if code == 2:
        print("  DO NOT CALL POST /v1/voice-changes with this file. It would "
              "convert and charge in full.")
    if code == 3:
        print("  Play it. If a person is talking, proceed; if not, stop.")
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
