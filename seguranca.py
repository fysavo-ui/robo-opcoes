import streamlit as st

def check_password():
    """Retorna True se a palavra-passe introduzida estiver correta."""
    def password_entered():
        # Compara com o segredo configurado no Streamlit Cloud
        if st.session_state["password"] == st.secrets.get("APP_PASSWORD", "admin123"):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Remove a palavra-passe da memória por segurança
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Introduza a palavra-passe de acesso:", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Introduza a palavra-passe de acesso:", type="password", on_change=password_entered, key="password")
        st.error("😕 Palavra-passe incorreta.")
        return False
    else:
        return True
