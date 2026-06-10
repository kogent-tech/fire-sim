interface Props {
  topic: string;
  label: string;
  onOpen: (topic: string) => void;
}

export default function InfoLink({ topic, label, onOpen }: Props) {
  return (
    <button type="button" className="info-link" aria-label={`What is ${label}?`} onClick={() => onOpen(topic)}>
      ?
    </button>
  );
}
