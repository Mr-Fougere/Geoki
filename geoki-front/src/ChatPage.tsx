import React, { useState } from "react";

type Props = {};

export default function ChatPage({}: Props) {
  const [town, setTown] = useState<String>("");
  const [postalCode, setPostalCode] = useState<String>("");
  const [number, setNumber] = useState<number>();
  const [subdivision, setSubdivision] = useState<String>("");
  const [street, setStreet] = useState<String>("");
  const [habitation, setHabitation] = useState<String>("");
  const [complement, setComplement] = useState<String>("");

  return (
    <div>
      <div>ChatPage</div>
    </div>
  );
}
