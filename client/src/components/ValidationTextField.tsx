import { TextField, type TextFieldProps } from "@mui/material"
import { type FC } from "react"
import type { FieldError, UseFormRegister } from "react-hook-form"

type ValidationTextFieldProps = {
    name: string
    label: string
    register: UseFormRegister<any>
    error?: FieldError
    rules?: Parameters<UseFormRegister<any>>[1]
} & Omit<TextFieldProps, "error">

export const ValidationTextField: FC<ValidationTextFieldProps> = ({name, label, register, error, rules, ...otherProps}) => {
    return (
        <TextField
            {...otherProps}
            label={label}
            error={!!error}
            helperText={error?.message}
            {...register(name, rules)}
        />
    );
}