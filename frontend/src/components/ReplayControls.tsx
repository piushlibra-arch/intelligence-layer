import React from 'react';
import {
  Play,
  Pause,
  RotateCcw,
  StepForward,
  StepBack,
  FastForward
} from 'lucide-react';
import './ReplayControls.css';

interface Props {
  isPlaying: boolean;
  isComplete: boolean;
  currentIndex: number;
  totalEvents: number;
  speed: number;
  loading: boolean;
  onPlay: () => void;
  onPause: () => void;
  onStepForward: () => void;
  onStepBackward: () => void;
  onReset: () => void;
  onSpeedChange: (speed: number) => void;
}

export const ReplayControls: React.FC<Props> = ({
  isPlaying,
  isComplete,
  currentIndex,
  totalEvents,
  speed,
  loading,
  onPlay,
  onPause,
  onStepForward,
  onStepBackward,
  onReset,
  onSpeedChange,
}) => {
  const speeds = [0.5, 1, 2, 5];

  return (
    <div className="replay-controls">
      <div className="replay-controls__playback">
        <button
          className="btn btn--secondary"
          onClick={onReset}
          disabled={loading || currentIndex === 0}
          title="Reset to beginning"
        >
          <RotateCcw size={16} />
          <span>Reset</span>
        </button>

        <button
          className="btn btn--secondary"
          onClick={onStepBackward}
          disabled={loading || isPlaying || currentIndex <= 0}
          title="Step backward one event"
        >
          <StepBack size={16} />
          <span>Prev</span>
        </button>

        {isPlaying ? (
          <button className="btn btn--primary" onClick={onPause} title="Pause simulation">
            <Pause size={16} />
            <span>Pause</span>
          </button>
        ) : (
          <button
            className="btn btn--primary"
            onClick={onPlay}
            disabled={loading || isComplete || totalEvents === 0}
            title="Start auto-play"
          >
            <Play size={16} />
            <span>Play</span>
          </button>
        )}

        <button
          className="btn btn--secondary"
          onClick={onStepForward}
          disabled={loading || isPlaying || isComplete || totalEvents === 0}
          title="Step forward one event"
        >
          <span>Next</span>
          <StepForward size={16} />
        </button>
      </div>

      <div className="replay-controls__progress">
        <div className="progress-bar-bg">
          <div
            className="progress-bar-fill"
            style={{ width: `${totalEvents > 0 ? (currentIndex / totalEvents) * 100 : 0}%` }}
          />
        </div>
        <span className="progress-text">
          Event {currentIndex} of {totalEvents}
        </span>
      </div>

      <div className="replay-controls__speed">
        <FastForward size={14} className="speed-icon" />
        <span className="speed-label">Speed:</span>
        <div className="speed-buttons">
          {speeds.map((s) => (
            <button
              key={s}
              className={`speed-btn ${speed === s ? 'speed-btn--active' : ''}`}
              onClick={() => onSpeedChange(s)}
            >
              {s}x
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
