import React, { useState } from 'react';
import './AddressForm.css'; // Assurez-vous de créer ce fichier CSS
type AddressFormData = {
  city: string;
  postalCode: string;
  number: string;
  street: string; // J'ai remplacé 'floor' et 'building' par 'street'
};

const AddressForm: React.FC = () => {
  const [formData, setFormData] = useState<AddressFormData>({
    city: '',
    postalCode: '',
    number: '',
    street: '',
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log(formData);
    // Ici, vous pouvez intégrer l'appel API pour valider l'adresse
  };

  return (
    <div className="address-form-container">
      <div className="title">Informations</div>
      <form onSubmit={handleSubmit} className="address-form">
      <div className="form-row">
          <label>
            N°
            <input
              type="text"
              name="number"
              value={formData.number}
              onChange={handleChange}
            />
          </label>
          <label>
            Voie
            <input
              type="text"
              name="street"
              value={formData.street}
              onChange={handleChange}
            />
          </label>
        </div>
        <div className="form-row">
          <label>
            Ville
            <input
              type="text"
              name="city"
              value={formData.city}
              onChange={handleChange}
            />
          </label>
          <label>
            Code postal
            <input
              type="text"
              name="postalCode"
              value={formData.postalCode}
              onChange={handleChange}
            />
          </label>
        </div>
        <button type="submit">Vérifier</button>
      </form>
    </div>
  );
};

export default AddressForm;
