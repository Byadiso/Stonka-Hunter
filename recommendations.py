# recommendations.py

def generate_recommendations(stonka_count, temperature):
    recommendations = []

    if stonka_count == 0:
        recommendations.append("✅ No immediate action required. Continue weekly monitoring.")
        recommendations.append("🌱 Maintain crop rotation and healthy soil to prevent outbreaks.")
        return recommendations

 
    if stonka_count <= 3:
        recommendations.append("🧤 Hand-pick beetles and larvae early in the morning.")
        recommendations.append("🪲 Encourage natural predators like ladybirds and ground beetles.")
    
   
    elif stonka_count <= 7:
        recommendations.append("🌿 Consider biological treatments (Neem oil, Bacillus thuringiensis).")
        recommendations.append("🔁 Rotate crops next season to break the beetle life cycle.")

   
    else:
        recommendations.append("⚠️ High infestation detected.")
        recommendations.append("🧪 Use selective insecticides only if other methods fail.")
        recommendations.append("📆 Avoid repeated use of the same chemical to prevent resistance.")

 
    if temperature is not None:
        if temperature < 15:
            recommendations.append("❄️ Low temperature: Beetle activity is reduced. Delay spraying.")
        elif temperature > 25:
            recommendations.append("☀️ High temperature: Apply treatments early morning or evening.")

    recommendations.append("📸 Keep photo records to track infestation trends over time.")
    return recommendations
