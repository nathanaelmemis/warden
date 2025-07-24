import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { Router } from './router/router'
import { createTheme, ThemeProvider } from '@mui/material/styles';
import './index.css'

let theme = createTheme()

theme = createTheme(theme, {
    palette: {
        primary: {
            main: "#0A494F",
            dark: "#041B1A"
        },
        secondary: {
            light: "#cfc79bff",
            main: "#9C9674",
            dark: "#757157ff",
        }
    }
});

createRoot(document.getElementById('root')!).render(
    <StrictMode>
        <ThemeProvider theme={theme}>
            <Router />
        </ThemeProvider>
    </StrictMode>,
)
