import { Box, Button, Stack, TextField, Typography } from "@mui/material";
import { Background } from "../components/Background";
import { useState, type ChangeEvent, type FC, type FormEvent } from "react";
import { ValidationTextField } from "../components/ValidationTextField";

export const Login: FC = () => {
    const [email, setEmail] = useState("")
    const [password, setPassword] = useState("")

    const handleSubmit = (event: FormEvent) => {
        event.preventDefault()

        // console.log(event.)
    }

    return (
        <Background
            display="flex"
            justifyContent="center"
            alignItems="center"
        >
            <Stack
                padding={4}
                spacing={2}
                borderRadius={2}
                width="20em"
                sx={{
                    backgroundColor: "secondary.main"
                }}
                component="form"
                onSubmit={handleSubmit}
            >
                <Typography 
                    variant="h3" fontWeight="bold">Warden</Typography>
                <ValidationTextField
                    label="Email"
                    value={email}
                    setValue={value => setEmail(value)}
                    required
                    pattern={/^nathan$/}
                />
                <ValidationTextField
                    label="Password"
                    value={password}
                    setValue={value => setPassword(value)}
                    required
                />
                <Box
                    display="flex"
                    justifyContent="right"
                >
                    <Button variant="contained" type="submit">Login</Button>
                </Box>
            </Stack>
        </Background>
    )
}