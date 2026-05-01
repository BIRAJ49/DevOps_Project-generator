export function InfinityLogo({ className = "", size = 56, title, ...props }) {
  const titleId = title ? "infinity-logo-title" : undefined;

  return (
    <svg
      className={className}
      width={size}
      height={Math.round(size * 0.58)}
      viewBox="0 0 180 92"
      fill="none"
      role={title ? "img" : "presentation"}
      aria-labelledby={titleId}
      aria-hidden={title ? undefined : true}
      {...props}
    >
      {title ? <title id={titleId}>{title}</title> : null}
      <path
        d="M28 46C28 23 45 17 61 17c15 0 26 11 39 29 13 18 24 29 39 29 16 0 25-12 25-29s-9-29-25-29c-15 0-26 11-39 29-13 18-24 29-39 29-16 0-33-6-33-29Z"
        stroke="#033f47"
        strokeWidth="24"
        strokeLinecap="butt"
        strokeLinejoin="round"
      />
      <path
        d="M28 46C28 23 45 17 61 17c15 0 26 11 39 29"
        stroke="#3f6788"
        strokeWidth="24"
        strokeLinecap="butt"
        strokeLinejoin="round"
      />
      <path
        d="M100 46c13-18 24-29 39-29 16 0 25 12 25 29"
        stroke="#79c88b"
        strokeWidth="24"
        strokeLinecap="butt"
        strokeLinejoin="round"
      />
      <path
        d="M164 46c0 17-9 29-25 29-15 0-26-11-39-29"
        stroke="#3f6788"
        strokeWidth="24"
        strokeLinecap="butt"
        strokeLinejoin="round"
      />
      <path
        d="M48 76 34 76 45 64"
        fill="#ffffff"
      />
      <path
        d="M75 20 98 43"
        stroke="#ffffff"
        strokeWidth="20"
        strokeLinecap="butt"
      />
      <path
        d="M115 73 103 73 105 60"
        fill="#ffffff"
      />
      <circle cx="61" cy="17" r="12" fill="#12b65a" />
      <path d="M137 17 154 17 154 35" fill="#12b65a" />
      <path
        d="M80 61 91 72"
        stroke="#12b65a"
        strokeWidth="9"
        strokeLinecap="butt"
      />
      <circle cx="152" cy="55" r="12" fill="#ffffff" />
    </svg>
  );
}
