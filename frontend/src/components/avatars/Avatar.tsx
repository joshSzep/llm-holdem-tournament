/**
 * Avatar component — displays player avatar with state indicators.
 */

import "./Avatar.css";

type AvatarState =
  | "default"
  | "active"
  | "folded"
  | "all-in"
  | "eliminated"
  | "low-chips";

interface AvatarProps {
  src: string;
  name: string;
  state?: AvatarState;
  size?: "small" | "medium" | "large";
}

export function Avatar({
  src,
  name,
  state = "default",
  size = "medium",
}: AvatarProps): React.ReactElement {
  return (
    <div className={`avatar avatar--${size} avatar--${state}`}>
      <img
        className="avatar__img"
        src={src}
        alt={name}
        onError={(e) => {
          (e.target as HTMLImageElement).src = "/avatars/default.png";
        }}
      />
      {state === "active" && <div className="avatar__glow" />}
    </div>
  );
}
