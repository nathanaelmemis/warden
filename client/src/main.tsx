import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { Router } from './routes'
import { createTheme, ThemeProvider } from '@mui/material/styles';
import './main.css'

let theme = createTheme()

theme = createTheme(theme, {
    palette: {
        primary: {
            main: "#0A494F",
            dark: "#041B1A"
        },
        secondary: {
            main: "#9C9674"
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
