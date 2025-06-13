import { TextField, type TextFieldProps } from "@mui/material";

export function StyledTextField(props: TextFieldProps) {
    return (
        <TextField
            // color="accent"
            {...props}
        />
    )
}