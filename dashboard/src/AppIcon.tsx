type Props = {
  size?: number;
  className?: string;
};

export default function AppIcon({ size = 32, className }: Props) {
  return (
    <svg
      className={className}
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <rect width="32" height="32" rx="9" fill="url(#icon-bg)" />
      <path
        d="M16 6L22 18H17.5L19 24L10 14H14.5L16 6Z"
        fill="url(#icon-bolt)"
        stroke="rgba(255,255,255,0.35)"
        strokeWidth="0.5"
        strokeLinejoin="round"
      />
      <circle cx="16" cy="16" r="11" stroke="rgba(255,255,255,0.12)" strokeWidth="1" />
      <defs>
        <linearGradient id="icon-bg" x1="4" y1="2" x2="28" y2="30">
          <stop stopColor="#0e7490" />
          <stop offset="1" stopColor="#059669" />
        </linearGradient>
        <linearGradient id="icon-bolt" x1="10" y1="6" x2="22" y2="24">
          <stop stopColor="#ecfeff" />
          <stop offset="1" stopColor="#a7f3d0" />
        </linearGradient>
      </defs>
    </svg>
  );
}
