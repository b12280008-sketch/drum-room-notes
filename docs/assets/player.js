const controls = document.querySelector("[data-player]");
const button = controls.querySelector("#play-pattern");
const tempo = controls.querySelector("#tempo");
const status = document.querySelector("#player-status");
const score = document.querySelector(".score");

// Use short synthetic sounds so each instrument is distinguishable.
const voices = {
  hat: { type: "square", start: 2500, end: 1650, seconds: 0.026, volume: 0.027 },
  snare: { type: "triangle", start: 410, end: 150, seconds: 0.075, volume: 0.08 },
  kick: { type: "sine", start: 120, end: 43, seconds: 0.13, volume: 0.15 },
};
const columns = Array.from({ length: 16 }, (_, i) => [...score.querySelectorAll(`[data-step="${i}"]`)]);
const notes = Array.from(score.querySelectorAll("tbody tr"), (row) => ({
  voice: voices[row.dataset.instrument],
  hits: Array.from(row.querySelectorAll("[data-hit]"), (cell) => cell.dataset.hit),
}));

let context;
let timer = null;
let frame = null;
let nextTime = 0;
let nextStep = 0;
let highlighted = -1;
let secondsPerStep = 0;
const pending = [];
const playing = new Set();

function sound(voice, time, accent) {
  const oscillator = context.createOscillator();
  const gain = context.createGain();
  oscillator.type = voice.type;
  oscillator.frequency.setValueAtTime(voice.start, time);
  oscillator.frequency.exponentialRampToValueAtTime(voice.end, time + voice.seconds);
  gain.gain.setValueAtTime(0.0001, time);
  gain.gain.exponentialRampToValueAtTime(voice.volume * (accent ? 1 : 0.66), time + 0.004);
  gain.gain.exponentialRampToValueAtTime(0.0001, time + voice.seconds);
  oscillator.connect(gain).connect(context.destination);
  playing.add(oscillator);
  oscillator.onended = () => {
    playing.delete(oscillator);
    oscillator.disconnect();
    gain.disconnect();
  };
  oscillator.start(time);
  oscillator.stop(time + voice.seconds);
}

function schedule() {
  const now = context.currentTime;
  if (nextTime < now) nextTime = now + 0.01;
  while (nextTime < now + 0.1) {
    for (const row of notes) {
      const hit = row.hits[nextStep];
      if (hit !== "-") sound(row.voice, nextTime, hit === "X");
    }
    pending.push({ step: nextStep, time: nextTime });
    nextStep = (nextStep + 1) % columns.length;
    nextTime += secondsPerStep;
  }
}

function paint() {
  let active = highlighted;
  while (pending.length && pending[0].time <= context.currentTime) active = pending.shift().step;
  if (active !== highlighted) {
    if (highlighted >= 0) columns[highlighted].forEach((cell) => cell.classList.remove("is-current"));
    columns[active].forEach((cell) => cell.classList.add("is-current"));
    highlighted = active;
  }
  frame = requestAnimationFrame(paint);
}

function stop() {
  if (timer === null) return;
  clearInterval(timer);
  cancelAnimationFrame(frame);
  timer = null;
  for (const oscillator of playing) oscillator.stop();
  pending.length = 0;
  if (highlighted >= 0) columns[highlighted].forEach((cell) => cell.classList.remove("is-current"));
  highlighted = -1;
  tempo.disabled = false;
  button.textContent = "播放節奏";
  button.setAttribute("aria-pressed", "false");
  status.textContent = "已停止。可以調整速度後再播放。";
}

button.addEventListener("click", async () => {
  if (timer !== null) {
    stop();
    return;
  }
  if (!tempo.reportValidity()) return;
  button.disabled = true;
  try {
    context ??= new AudioContext();
    await context.resume();
    if (document.hidden) return;
    const bpm = tempo.valueAsNumber;
    secondsPerStep = 60 / (bpm * 4);
    nextTime = context.currentTime + 0.045;
    nextStep = 0;
    schedule();
    timer = setInterval(schedule, 25);
    frame = requestAnimationFrame(paint);
    tempo.disabled = true;
    button.textContent = "停止播放";
    button.setAttribute("aria-pressed", "true");
    status.textContent = `正在以 ${bpm} BPM 循環播放。`;
  } catch {
    status.textContent = "音訊未能啟動，仍可以依照節奏譜練習。";
  } finally {
    button.disabled = false;
  }
});

document.addEventListener("visibilitychange", () => {
  if (document.hidden) stop();
});
window.addEventListener("pagehide", stop);
