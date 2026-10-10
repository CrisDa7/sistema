export default function Card({ children, className = '' }) {
  return (
    <div className={`bg-[#111111] border border-[#272727] rounded-2xl p-6 ${className}`}>
      {children}
    </div>
  );
}
