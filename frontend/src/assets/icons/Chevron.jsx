

export const Chevron = ({ open }) => (
    <svg
      className={`w-5 h-5 transition-transform duration-200 ${open ? "-rotate-90" : "rotate-90"}`}
      viewBox="0 0 20 20"
      fill="currentColor"
      aria-hidden="true"
    >
      <path d="M7 5l6 5-6 5V5z" />
    </svg>
  );