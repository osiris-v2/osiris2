// /var/osiris2/seed/aichat_server/src/types.rs
use serde::{Deserialize, Serialize};

// --- ESTRUCTURAS ---
#[derive(Deserialize, Serialize, Clone)]
pub struct TVChannel {
    pub canal: String,
    pub url: String,
}
